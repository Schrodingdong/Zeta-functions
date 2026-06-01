package com.schrodi.zeta_runner.service;

import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.zip.ZipFile;

import com.schrodi.zeta_runner.docker.DockerClient;
import com.schrodi.zeta_runner.docker.DockerClientException;
import com.schrodi.zeta_runner.dto.SpawnZetaResponse;
import com.schrodi.zeta_runner.utils.ZipUtils;
import io.kubernetes.client.openapi.ApiClient;
import io.kubernetes.client.openapi.ApiException;
import io.kubernetes.client.openapi.apis.AppsV1Api;
import io.kubernetes.client.openapi.apis.CoreV1Api;
import io.kubernetes.client.openapi.models.V1Deployment;
import io.kubernetes.client.openapi.models.V1DeploymentList;
import io.kubernetes.client.openapi.models.V1Service;
import org.jspecify.annotations.NonNull;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.io.Resource;
import org.springframework.core.io.ResourceLoader;
import org.springframework.stereotype.Service;

import com.schrodi.zeta_runner.config.MinioConfig;

import io.minio.GetObjectArgs;
import io.minio.GetObjectResponse;
import io.minio.MinioClient;

@Service
public class RunnerService {
    private static final String BASE_IMAGE = "zeta-base-runner-python:0.0.1";
    private static final String NAMESPACE = "default";
    private static final Logger log = LoggerFactory.getLogger(RunnerService.class);
    private final MinioConfig minioConfig;
    private final ResourceLoader resourceLoader;
    private final CoreV1Api coreV1Api;
    private final AppsV1Api appsV1Api;

    public RunnerService(
            MinioConfig minioConfig,
            ResourceLoader resourceLoader,
            CoreV1Api coreV1Api,
            AppsV1Api appsV1Api) {
        this.minioConfig = minioConfig;
        this.resourceLoader = resourceLoader;
        this.coreV1Api = coreV1Api;
        this.appsV1Api = appsV1Api;
    }

    public SpawnZetaResponse spawnZeta(String zetaName) {
        // Check if the zeta has been deployed
        try {
            if (isZetaDeployed(zetaName)) {
                log.info("Zeta {} already deployed", zetaName);
                var deployment = appsV1Api.listNamespacedDeployment(NAMESPACE)
                        .execute()
                        .getItems()
                        .stream()
                        .filter(i -> i.getMetadata().getName().equals(zetaName))
                        .findFirst()
                        .orElseThrow();
                var service = coreV1Api.listNamespacedService(NAMESPACE)
                        .execute()
                        .getItems()
                        .stream()
                        .filter(i -> i.getMetadata().getName().equals(zetaName))
                        .findFirst()
                        .orElseThrow();
                return new SpawnZetaResponse(
                        zetaName,
                        deployment.getMetadata().getName(),
                        service.getMetadata().getName()
                );
            }
        } catch (Exception e) {
            throw new RuntimeException(e);
        }

        // Retrieve the user's code from objectStorage
        MinioClient client = MinioClient.builder()
            .endpoint(minioConfig.getEndpoint())
            .credentials(minioConfig.getUsername(), minioConfig.getPassword())
            .build();
        GetObjectArgs getObjectArgs = GetObjectArgs.builder()
            .bucket(minioConfig.getBucket())
            .object(zetaName + ".zip")
            .build();

        // Get the ZIP in local tmp
        Path zetaTmpDirPath;
        Path zipPath;
        try (GetObjectResponse res = client.getObject(getObjectArgs)) {
            zetaTmpDirPath = Files.createTempDirectory(zetaName + "_");
            zipPath = Files.createTempFile(zetaTmpDirPath, zetaName+"_", ".zip");
            Files.write(zipPath, res.readAllBytes());
            log.info("Tmp zip path: {}", zipPath.toAbsolutePath());
        } catch (Exception e) {
            throw new RuntimeException(e);
        }

        // unzip the files
        try {
            ZipUtils.unzip(zipPath, zetaTmpDirPath);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }

        // Add dockerfile
        try {
            Path dockerfilePath = Files.createFile(Path.of(zetaTmpDirPath.toString(), "Dockerfile"));
            String dockerfileContent = getRunnerDockerfile(BASE_IMAGE);
            Files.write(dockerfilePath, dockerfileContent.getBytes());
            log.info("Docker file path: {}", dockerfilePath.toAbsolutePath());
        } catch (Exception e) {
            throw new RuntimeException(e);
        }

        // Build the image
        DockerClient dockerClient = new DockerClient();
        String imageName = zetaName + "-runner:0.0.1-" + Instant.now().toEpochMilli();
        try {
            dockerClient.buildImage(imageName, zetaTmpDirPath);
        } catch (DockerClientException e) {
            throw new RuntimeException(e);
        }

        // Push to registry
        /*try {
            dockerClient.pushToRegistry(imageName);
        } catch (DockerClientException e) {
            throw new RuntimeException(e);
        }*/

        // deploy the zeta
        String deploymentName;
        String serviceName;
        try {
            // Create deployment
            String deploymentJson = getDeployment(zetaName, imageName);
            V1Deployment deployment = appsV1Api.createNamespacedDeployment(
                    NAMESPACE,
                    V1Deployment.fromJson(deploymentJson)
            ).execute();
            deploymentName = deployment.getMetadata().getName();
            log.info("Deployment created: {}", deployment.getMetadata().getName());

            // Create a service
            String serviceJson = getService(zetaName);
            V1Service service = coreV1Api.createNamespacedService(
                    NAMESPACE,
                    V1Service.fromJson(serviceJson)
            ).execute();
            serviceName = service.getMetadata().getName();
            log.info("Service created: {}", service.getMetadata().getName());
            log.info("> Service port: {}", service.getSpec().getPorts().get(0).getPort());
            log.info("> Service NodePort: {}", service.getSpec().getPorts().get(0).getNodePort());
        } catch (Exception e) {
            throw new RuntimeException(e);
        }

        return new SpawnZetaResponse(zetaName, deploymentName, serviceName);
    }

    private boolean isZetaDeployed(String zetaName) throws ApiException {
        V1DeploymentList list = appsV1Api.listNamespacedDeployment(NAMESPACE).execute();
        V1Deployment deployment = list.getItems()
                .stream()
                .filter(i -> i.getMetadata().getName().equals(zetaName))
                .findFirst()
                .orElse(null);
        return deployment != null;
    }

    /**
     * Returns the Zeta runner Dockerfile
     * @param baseImage The base Zeta runner image
     */
    private String getRunnerDockerfile(String baseImage) throws IOException {
        return resourceLoader
                .getResource("classpath:runner-dockerfiles/python-dockerfile")
                .getContentAsString(Charset.defaultCharset())
                .replaceAll("%BASE_IMAGE%", baseImage);
    }

    /**
     * Returns JSON deployment manifest
     * @param zeta Zeta name
     * @param image The runner's image
     */
    private String getDeployment(String zeta, String image) throws IOException {
        return resourceLoader
                .getResource("classpath:k8s/deployment.json")
                .getContentAsString(Charset.defaultCharset())
                .replaceAll("%ZETA_NAME%", zeta)
                .replaceAll("%RUNNER_IMAGE%", image);
    }

    /**
     * Returns JSON service manifest
     * @param zeta Zeta name
     */
    private @NonNull String getService(String zeta) throws IOException {
        return resourceLoader
                .getResource("classpath:k8s/service.json")
                .getContentAsString(Charset.defaultCharset())
                .replaceAll("%ZETA_NAME%", zeta);
    }
}

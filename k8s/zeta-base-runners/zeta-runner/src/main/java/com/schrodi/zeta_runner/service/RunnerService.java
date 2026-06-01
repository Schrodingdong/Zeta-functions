package com.schrodi.zeta_runner.service;

import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.zip.ZipFile;

import com.schrodi.zeta_runner.docker.DockerClient;
import com.schrodi.zeta_runner.docker.DockerClientException;
import com.schrodi.zeta_runner.dto.SpawnZetaResponse;
import com.schrodi.zeta_runner.model.ZetaRunner;
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
import org.springframework.core.io.ResourceLoader;
import org.springframework.stereotype.Service;

import com.schrodi.zeta_runner.config.MinioConfig;

import io.minio.GetObjectArgs;
import io.minio.GetObjectResponse;
import io.minio.MinioClient;
import tools.jackson.databind.ObjectMapper;

@Service
public class RunnerService {
    private static final String PREFIX = "zeta-";
    private static final String BASE_IMAGE = "zeta-base-runner-python:0.0.1";
    private static final String NAMESPACE = "default";
    private static final Logger log = LoggerFactory.getLogger(RunnerService.class);
    private final MinioConfig minioConfig;
    private final ResourceLoader resourceLoader;
    private final CoreV1Api coreV1Api;
    private final AppsV1Api appsV1Api;
    private final ObjectMapper objectMapper;

    public RunnerService(
            MinioConfig minioConfig,
            ResourceLoader resourceLoader,
            CoreV1Api coreV1Api,
            AppsV1Api appsV1Api,
            ObjectMapper objectMapper
    ) {
        this.minioConfig = minioConfig;
        this.resourceLoader = resourceLoader;
        this.coreV1Api = coreV1Api;
        this.appsV1Api = appsV1Api;
        this.objectMapper = objectMapper;
    }

    /**
     * Returns all deployed zeta runners
     */
    public List<ZetaRunner> getZetaRunners() {
        try {
            var deployments = appsV1Api.listNamespacedDeployment(NAMESPACE)
                    .execute()
                    .getItems()
                    .stream()
                    .filter(i -> i.getMetadata().getName().startsWith(PREFIX))
                    .toList();
            var services = coreV1Api.listNamespacedService(NAMESPACE)
                    .execute()
                    .getItems()
                    .stream()
                    .filter(i -> i.getMetadata().getName().startsWith(PREFIX))
                    .toList();

            List<ZetaRunner> runners = new ArrayList<>();
            for (var deployment : deployments) {
                String zeta = deployment.getMetadata().getName();
                var service = services
                        .stream()
                        .filter(i -> i.getMetadata().getName().equals(zeta))
                        .findFirst()
                        .orElseThrow();
                runners.add(
                        new ZetaRunner(
                                zeta,
                                Map.of(
                                        "deployment", objectMapper.readTree(deployment.toJson()),
                                        "service", objectMapper.readTree(service.toJson())
                                )
                        )
                );
            }
            return runners;
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    /**
     * Return dynamic details for the Zeta runner
     */
    public ZetaRunner getZetaRunner(String zeta) {
        try {
            var deployment = appsV1Api.listNamespacedDeployment(NAMESPACE)
                    .execute()
                    .getItems()
                    .stream()
                    .filter(i -> i.getMetadata().getName().equals(zeta))
                    .findFirst()
                    .orElseThrow();
            var service = coreV1Api.listNamespacedService(NAMESPACE)
                    .execute()
                    .getItems()
                    .stream()
                    .filter(i -> i.getMetadata().getName().equals(zeta))
                    .findFirst()
                    .orElseThrow();
            return new ZetaRunner(
                zeta,
                Map.of(
                        "deployment", objectMapper.readTree(deployment.toJson()),
                        "service", objectMapper.readTree(service.toJson())
                )
            );
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    /**
     * Spawn a Zeta
     */
    public SpawnZetaResponse spawnZeta(String zeta) {
        String zetaWithPrefix = PREFIX + zeta;
        // Check if the zeta has been deployed
        try {
            if (isZetaDeployed(zetaWithPrefix)) {
                log.info("Zeta {} already deployed", zetaWithPrefix);
                var deployment = appsV1Api.listNamespacedDeployment(NAMESPACE)
                        .execute()
                        .getItems()
                        .stream()
                        .filter(i -> i.getMetadata().getName().equals(zetaWithPrefix))
                        .findFirst()
                        .orElseThrow();
                var service = coreV1Api.listNamespacedService(NAMESPACE)
                        .execute()
                        .getItems()
                        .stream()
                        .filter(i -> i.getMetadata().getName().equals(zetaWithPrefix))
                        .findFirst()
                        .orElseThrow();
                return new SpawnZetaResponse(
                        zeta,
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
            .object(zeta + ".zip")
            .build();

        // Get the ZIP in local tmp
        Path zetaTmpDirPath;
        Path zipPath;
        try (GetObjectResponse res = client.getObject(getObjectArgs)) {
            zetaTmpDirPath = Files.createTempDirectory(zetaWithPrefix + "_");
            zipPath = Files.createTempFile(zetaTmpDirPath, zetaWithPrefix + "_", ".zip");
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
        String imageName = zetaWithPrefix + "-runner:0.0.1-" + Instant.now().toEpochMilli();
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
            String deploymentJson = getDeployment(zetaWithPrefix, imageName);
            V1Deployment deployment = appsV1Api.createNamespacedDeployment(
                    NAMESPACE,
                    V1Deployment.fromJson(deploymentJson)
            ).execute();
            deploymentName = deployment.getMetadata().getName();
            log.info("Deployment created: {}", deployment.getMetadata().getName());

            // Create a service
            String serviceJson = getService(zetaWithPrefix);
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

        return new SpawnZetaResponse(zeta, deploymentName, serviceName);
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

    public void deleteZeta(String zeta) {
        try {
            String zetaWithPrefix = PREFIX + zeta;
            var deploymentName = appsV1Api.listNamespacedDeployment(NAMESPACE)
                    .execute()
                    .getItems()
                    .stream()
                    .filter(i -> i.getMetadata().getName().equals(zetaWithPrefix))
                    .findFirst()
                    .orElseThrow()
                    .getMetadata()
                    .getName();
            var serviceName = coreV1Api.listNamespacedService(NAMESPACE)
                    .execute()
                    .getItems()
                    .stream()
                    .filter(i -> i.getMetadata().getName().equals(zetaWithPrefix))
                    .findFirst()
                    .orElseThrow()
                    .getMetadata()
                    .getName();
            appsV1Api.deleteNamespacedDeployment(deploymentName, NAMESPACE).execute();
            coreV1Api.deleteNamespacedService(serviceName, NAMESPACE).execute();
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }
}

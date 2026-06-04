package com.schrodi.zeta_runner.service;

import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

import com.schrodi.zeta_runner.config.RegistryConfig;
import com.schrodi.zeta_runner.docker.DockerClient;
import com.schrodi.zeta_runner.docker.DockerClientException;
import com.schrodi.zeta_runner.dto.ZetaRunnerResponse;
import com.schrodi.zeta_runner.exceptions.ZetaNotDeployedException;
import com.schrodi.zeta_runner.exceptions.ZetaResourceNotFoundException;
import com.schrodi.zeta_runner.model.*;
import com.schrodi.zeta_runner.utils.ZipUtils;
import io.kubernetes.client.openapi.ApiException;
import io.kubernetes.client.openapi.apis.AppsV1Api;
import io.kubernetes.client.openapi.apis.AutoscalingV2Api;
import io.kubernetes.client.openapi.apis.CoreV1Api;
import io.kubernetes.client.openapi.models.V1Deployment;
import io.kubernetes.client.openapi.models.V1Service;
import io.kubernetes.client.openapi.models.V2HorizontalPodAutoscaler;
import org.jspecify.annotations.NonNull;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ResourceLoader;
import org.springframework.stereotype.Service;

import com.schrodi.zeta_runner.config.MinioConfig;

import io.minio.GetObjectArgs;
import io.minio.GetObjectResponse;
import io.minio.MinioClient;

@Service
public class RunnerService {
    private static final String PREFIX = "zeta-";
    private static final String NAMESPACE = "default";
    private static final Logger log = LoggerFactory.getLogger(RunnerService.class);

    @Value("${app.runner.base-image}")
    private String BASE_IMAGE;
    @Value("${app.runner.version}")
    private String RUNNER_VERSION;

    private final MinioConfig minioConfig;
    private final ResourceLoader resourceLoader;
    private final CoreV1Api coreV1Api;
    private final AppsV1Api appsV1Api;
    private final AutoscalingV2Api autoscalingV2Api;
    private final DockerClient dockerClient;
    private final RegistryConfig registryConfig;

    public RunnerService(
            MinioConfig minioConfig,
            ResourceLoader resourceLoader,
            CoreV1Api coreV1Api,
            AppsV1Api appsV1Api,
            AutoscalingV2Api autoscalingV2Api,
            DockerClient dockerClient,
            RegistryConfig registryConfig
    ) {
        this.minioConfig = minioConfig;
        this.resourceLoader = resourceLoader;
        this.coreV1Api = coreV1Api;
        this.appsV1Api = appsV1Api;
        this.autoscalingV2Api = autoscalingV2Api;
        this.dockerClient = dockerClient;
        this.registryConfig = registryConfig;
    }

    /**
     * Returns all deployed zeta runners
     */
    public List<ZetaRunnerResponse> getZetaRunners() {
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
            var hpas = autoscalingV2Api.listNamespacedHorizontalPodAutoscaler(NAMESPACE)
                    .execute()
                    .getItems()
                    .stream()
                    .filter(i -> i.getMetadata().getName().startsWith(PREFIX))
                    .toList();

            List<ZetaRunnerResponse> runners = new ArrayList<>();
            for (var deployment : deployments) {
                String zeta = deployment.getMetadata().getName();
                var service = services
                        .stream()
                        .filter(i -> i.getMetadata().getName().equals(zeta))
                        .findFirst()
                        .orElseThrow();
                var hpa = hpas
                        .stream()
                        .filter(i -> i.getMetadata().getName().equals(zeta))
                        .findFirst()
                        .orElseThrow();
                runners.add(
                        new ZetaRunnerResponse(
                                zeta,
                                ZetaDRDeployment.from(deployment),
                                ZetaDRService.from(service),
                                ZetaDRHPA.from(hpa)
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
    public ZetaRunnerResponse getZetaRunner(String zeta) {
        String zetaDRN = getZetaDeploymentResourceName(zeta);
        try {
            var deployment = appsV1Api.listNamespacedDeployment(NAMESPACE)
                    .execute()
                    .getItems()
                    .stream()
                    .filter(i -> i.getMetadata().getName().equals(zetaDRN))
                    .findFirst()
                    .orElseThrow(() -> new ZetaResourceNotFoundException(zeta, ZetaDeploymentResourceType.DEPLOYMENT));
            var service = coreV1Api.listNamespacedService(NAMESPACE)
                    .execute()
                    .getItems()
                    .stream()
                    .filter(i -> i.getMetadata().getName().equals(zetaDRN))
                    .findFirst()
                    .orElseThrow(() -> new ZetaResourceNotFoundException(zeta, ZetaDeploymentResourceType.SERVICE));
            var hpa = autoscalingV2Api.listNamespacedHorizontalPodAutoscaler(NAMESPACE)
                    .execute()
                    .getItems()
                    .stream()
                    .filter(i -> i.getMetadata().getName().equals(zetaDRN))
                    .findFirst()
                    .orElseThrow(() -> new ZetaResourceNotFoundException(zeta, ZetaDeploymentResourceType.HPA));
            return new ZetaRunnerResponse(
                    zeta,
                    ZetaDRDeployment.from(deployment),
                    ZetaDRService.from(service),
                    ZetaDRHPA.from(hpa)
            );
        } catch (ApiException e) {
            throw new RuntimeException(e);
        }
    }

    /**
     * Spawn a Zeta
     */
    public ZetaRunnerResponse spawnZeta(String zeta) {
        String zetaDRN = getZetaDeploymentResourceName(zeta);

        // Retrieve the user's code from objectStorage
        MinioClient client = MinioClient.builder()
            .endpoint(minioConfig.getServiceUrl())
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
            zetaTmpDirPath = Files.createTempDirectory(zetaDRN + "_");
            zipPath = Files.createTempFile(zetaTmpDirPath, zetaDRN + "_", ".zip");
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
            String dockerfile = getRunnerDockerfile();
            Files.write(dockerfilePath, dockerfile.getBytes());
            log.info("Docker file path: {}", dockerfilePath.toAbsolutePath());
        } catch (Exception e) {
            throw new RuntimeException(e);
        }

        // Build the image
        String image = String.format("%s-runner:%s-%d", zetaDRN, RUNNER_VERSION, Instant.now().toEpochMilli());
        try {
            dockerClient.buildImage(image, zetaTmpDirPath);
        } catch (DockerClientException e) {
            throw new RuntimeException(e);
        }

        // Tag the image
        String registryUrl = registryConfig.getServiceUrl();
        String taggedImage = String.format("%s/%s",  registryUrl.replaceAll("http://", ""), image);
        try {
            dockerClient.tagImage(image, taggedImage);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }

        // Push to registry
        try {
            dockerClient.pushToRegistry(taggedImage);
        } catch (DockerClientException e) {
            throw new RuntimeException(e);
        }

        // deploy the zeta
        V1Deployment deployment;
        V1Service service;
        V2HorizontalPodAutoscaler hpa;
        try {
            // Create deployment
            String deploymentJson = getDeployment(zetaDRN, image);
            deployment = appsV1Api.createNamespacedDeployment(
                    NAMESPACE,
                    V1Deployment.fromJson(deploymentJson)
            ).execute();
            log.info("Deployment created: {}", deployment.getMetadata().getName());

            // Create HPA
            String hpaJson = getHpa(zetaDRN);
            hpa = autoscalingV2Api.createNamespacedHorizontalPodAutoscaler(
                    NAMESPACE,
                    V2HorizontalPodAutoscaler.fromJson(hpaJson)
            ).execute();
            log.info("HPA created: {}", hpa.getMetadata().getName());

            // Create a service
            String serviceJson = getService(zetaDRN);
            service = coreV1Api.createNamespacedService(
                    NAMESPACE,
                    V1Service.fromJson(serviceJson)
            ).execute();
            log.info("Service created: {}", service.getMetadata().getName());
            log.info("> Service port: {}", service.getSpec().getPorts().get(0).getPort());
            log.info("> Service NodePort: {}", service.getSpec().getPorts().get(0).getNodePort());
        } catch (Exception e) {
            throw new RuntimeException(e);
        }

        return new ZetaRunnerResponse(
                zeta,
                ZetaDRDeployment.from(deployment),
                ZetaDRService.from(service),
                ZetaDRHPA.from(hpa)
        );
    }

    /**
     * Delete Zeta runner deployment resources
     */
    public void deleteZetaRunner(String zeta) {
        String zetaDRN = getZetaDeploymentResourceName(zeta);
        try {
            appsV1Api.deleteNamespacedDeployment(zetaDRN, NAMESPACE).execute();
        } catch (ApiException e) {
            log.error("Error deleting deployment '{}': {}", zetaDRN, e.getResponseBody());
        }
        try {
            autoscalingV2Api.deleteNamespacedHorizontalPodAutoscaler(zetaDRN, NAMESPACE).execute();
        } catch (ApiException e) {
            log.error("Error deleting HPA '{}': {}", zetaDRN, e.getResponseBody());
        }
        try {
            coreV1Api.deleteNamespacedService(zetaDRN, NAMESPACE).execute();
        } catch (ApiException e) {
            log.error("Error deleting Service '{}': {}", zetaDRN, e.getResponseBody());
        }
    }

    /**
     * Returns the Zeta runner Dockerfile
     */
    private String getRunnerDockerfile() throws IOException {
        return resourceLoader
                .getResource("classpath:runner-dockerfiles/python-dockerfile")
                .getContentAsString(Charset.defaultCharset())
                .replaceAll("%BASE_IMAGE%", BASE_IMAGE);
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
                .replaceAll("%ZETA_NAMESPACE%", NAMESPACE)
                .replaceAll("%ZETA_NAME%", zeta)
                .replaceAll("%RUNNER_IMAGE%", image);
    }

    /**
     * Returns JSON HPA manifest
     * @param zeta Zeta name
     */
    private String getHpa(String zeta) throws IOException {
        return resourceLoader
                .getResource("classpath:k8s/hpa.json")
                .getContentAsString(Charset.defaultCharset())
                .replaceAll("%ZETA_NAMESPACE%", NAMESPACE)
                .replaceAll("%ZETA_NAME%", zeta);
    }

    /**
     * Returns JSON service manifest
     * @param zeta Zeta name
     */
    private @NonNull String getService(String zeta) throws IOException {
        return resourceLoader
                .getResource("classpath:k8s/service.json")
                .getContentAsString(Charset.defaultCharset())
                .replaceAll("%ZETA_NAMESPACE%", NAMESPACE)
                .replaceAll("%ZETA_NAME%", zeta);
    }

    /**
     * Returns the deployment resource name for the specified zeta
     * <p>
     * This will simply be the zeta name prefixed with {@code PREFIX}
     */
    private String getZetaDeploymentResourceName(String zeta) {
        return PREFIX + zeta;
    }
}

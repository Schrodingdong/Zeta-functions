package com.schrodi.zeta_runner.docker;

import com.schrodi.zeta_runner.config.RegistryConfig;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.file.Path;

@Component
public class DockerClient {
    private static final Logger log = LoggerFactory.getLogger(DockerClient.class);

    public void tagImage(String imageName, String newTag) throws DockerClientException {
        try {
            ProcessBuilder pb = new ProcessBuilder(
                    "docker",
                    "tag",
                    imageName,
                    newTag
            );
            Process process = pb.start();
            StringBuilder error = new StringBuilder();
            try  (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    error.append(line);
                }
            }
            int exitCode = process.waitFor();
            log.error(error.toString());
            if (exitCode != 0) {
                throw new DockerClientException(String.format("Exit code %d", exitCode));
            }
            log.info("Tagged image '{}' with '{}'", imageName, newTag);
        } catch (Exception e) {
            String msg = String.format("Error tagging container image %s with %s", imageName, newTag);
            throw new DockerClientException(msg, e);
        }

    }

    /**
     * Push image to the configured Image registry
     */
    public void pushToRegistry(String imageName) throws DockerClientException {
        try {
            ProcessBuilder pb = new ProcessBuilder(
                    "docker",
                    "push",
                    imageName
            );
            Process process = pb.start();
            StringBuilder error = new StringBuilder();
            try  (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    error.append(line);
                }
            }
            int exitCode = process.waitFor();
            log.error(error.toString());
            if (exitCode != 0) {
                throw new DockerClientException(String.format("Exit code %d", exitCode));
            }
            log.info("Image '{}' pushed to registry", imageName);
        } catch (Exception e) {
            String msg = String.format("Error pushing container image %s to registry", imageName);
            throw new DockerClientException(msg, e);
        }

    }

    /**
     * Build the container image
     */
    public void buildImage(String imageName, Path workspaceDir) throws DockerClientException {
        try {
            ProcessBuilder pb = new ProcessBuilder(
                    "docker",
                    "build",
                    "-t",
                    imageName,
                    workspaceDir.toString()
            );
            Process process = pb.start();
            int exitCode = process.waitFor();
            if (exitCode != 0) {
                throw new DockerClientException(String.format("Exit code %d", exitCode));
            }
            log.info("Container image '{}' built", imageName);
        } catch (Exception e) {
            String msg = String.format("Error building docker image %s", imageName);
            throw new DockerClientException(msg, e);
        }
    }
}

package com.schrodi.zeta_runner.docker;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.file.Path;

public class DockerClient {
    private static final Logger log = LoggerFactory.getLogger(DockerClient.class);

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
        } catch (Exception e) {
            String msg = String.format("Error building docker image %s", imageName);
            throw new DockerClientException(msg, e);
        }

    }

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
        } catch (Exception e) {
            String msg = String.format("Error building docker image %s", imageName);
            throw new DockerClientException(msg, e);
        }
    }
}

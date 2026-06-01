package com.schrodi.zeta_runner.docker;

public class DockerClientException extends Exception {
    public DockerClientException(String message) {
        super(message);
    }

    public DockerClientException(String message, Throwable e) {
        super(message, e);
    }
}

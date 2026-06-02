package com.schrodi.zetaapiserver.exception;

public class ZetaDeploymentException extends RuntimeException {
    public ZetaDeploymentException(String message, Throwable cause) {
        super(message, cause);
    }
    public ZetaDeploymentException(String message) {
        super(message);
    }
}

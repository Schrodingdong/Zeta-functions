package com.schrodi.zetaapiserver.exception;

public class ZetaResourceNotFoundException extends RuntimeException {
    public ZetaResourceNotFoundException(String message, Throwable cause) {
        super(message, cause);
    }
}

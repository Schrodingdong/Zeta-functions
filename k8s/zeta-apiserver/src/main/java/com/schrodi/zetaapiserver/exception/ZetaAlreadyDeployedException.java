package com.schrodi.zetaapiserver.exception;

public class ZetaAlreadyDeployedException extends RuntimeException {
    public ZetaAlreadyDeployedException(String zeta) {
        super(String.format("Zeta '%s' already exists", zeta));
    }
}

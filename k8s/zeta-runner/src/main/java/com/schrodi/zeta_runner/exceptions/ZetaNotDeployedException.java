package com.schrodi.zeta_runner.exceptions;

public class ZetaNotDeployedException extends RuntimeException {
    public ZetaNotDeployedException(String zeta) {
        super(String.format("Zeta '%s' is not deployed", zeta));
    }
}

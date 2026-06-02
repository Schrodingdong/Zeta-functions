package com.schrodi.zeta_runner.exceptions;

import com.schrodi.zeta_runner.model.ZetaDeploymentResourceType;

public class ZetaResourceNotFoundException extends RuntimeException {
    public ZetaResourceNotFoundException(String zeta, ZetaDeploymentResourceType resource) {
        super(String.format("Zeta resource '%s' not found for '%s'", resource, zeta));
    }
}

package com.schrodi.zetaapiserver.dto;

import java.io.Serializable;

public record DeploymentTask (
        String zetaName
) implements Serializable { }

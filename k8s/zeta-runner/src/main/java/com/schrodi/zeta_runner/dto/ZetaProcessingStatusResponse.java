package com.schrodi.zeta_runner.dto;

import com.schrodi.zeta_runner.model.ZetaStatus;

import java.io.Serializable;

public record ZetaProcessingStatusResponse(
        ZetaStatus status,
        String msg
) implements Serializable { }

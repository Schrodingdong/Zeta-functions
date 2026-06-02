package com.schrodi.zetaapiserver.dto;

import com.schrodi.zetaapiserver.model.ZetaStatus;

import java.io.Serializable;

public record ZetaProcessingStatusResponse(
        ZetaStatus status,
        String msg
) implements Serializable { }

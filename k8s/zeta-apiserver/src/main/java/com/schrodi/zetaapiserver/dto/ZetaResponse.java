package com.schrodi.zetaapiserver.dto;

import com.schrodi.zetaapiserver.model.ZetaStatus;

import java.util.UUID;

public record ZetaResponse(
        UUID id,
        String name,
        ZetaStatus status
) { }

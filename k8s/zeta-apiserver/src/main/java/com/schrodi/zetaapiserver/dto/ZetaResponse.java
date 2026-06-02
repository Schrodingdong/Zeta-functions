package com.schrodi.zetaapiserver.dto;

import com.schrodi.zetaapiserver.model.ZetaStatus;

public record ZetaResponse(
    String zetaName,
    ZetaStatus status
) { }

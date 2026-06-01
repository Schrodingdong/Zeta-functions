package com.schrodi.zeta_runner.dto;

public record SpawnZetaResponse(
    String zetaName,
    String deploymentName,
    String serviceName
) { }

package com.schrodi.zeta_runner.model;

public record ZetaRunner(
    String name,
    ZetaDRDeployment zetaDRDeployment,
    ZetaDRService zetaDRService
) { }

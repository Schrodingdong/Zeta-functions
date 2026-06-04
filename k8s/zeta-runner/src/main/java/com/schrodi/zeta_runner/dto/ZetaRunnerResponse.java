package com.schrodi.zeta_runner.dto;

import com.schrodi.zeta_runner.model.ZetaDRDeployment;
import com.schrodi.zeta_runner.model.ZetaDRHPA;
import com.schrodi.zeta_runner.model.ZetaDRService;

public record ZetaRunnerResponse(
    String zetaName,
    ZetaDRDeployment deployment,
    ZetaDRService service,
    ZetaDRHPA hpa
) { }

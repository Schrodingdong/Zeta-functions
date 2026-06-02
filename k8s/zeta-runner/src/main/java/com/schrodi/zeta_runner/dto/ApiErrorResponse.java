package com.schrodi.zeta_runner.dto;

import java.time.LocalDateTime;

public record ApiErrorResponse(
    String message,
    LocalDateTime timestamp
) { }
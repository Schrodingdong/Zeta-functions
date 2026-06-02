package com.schrodi.zetaapiserver.dto;

import java.time.LocalDateTime;

public record ApiErrorResponse(
        String message,
        LocalDateTime timestamp
) { }

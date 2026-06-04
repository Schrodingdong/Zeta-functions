package com.schrodi.zetaapiserver.dto;

import com.schrodi.zetaapiserver.model.Zeta;
import com.schrodi.zetaapiserver.model.ZetaStatus;
import jakarta.persistence.Column;
import org.hibernate.annotations.UpdateTimestamp;

import java.time.LocalDateTime;
import java.util.UUID;

public record ZetaResponse(
        UUID id,
        String name,
        ZetaStatus status,
        LocalDateTime createdAt,
        LocalDateTime updatedAt
) {
    public ZetaResponse(Zeta zeta) {
        this(zeta.getId(), zeta.getName(), zeta.getZetaStatus(), zeta.getCreatedAt(), zeta.getUpdatedAt());
    }
}

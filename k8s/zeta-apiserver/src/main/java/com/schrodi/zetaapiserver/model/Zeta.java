package com.schrodi.zetaapiserver.model;

import jakarta.persistence.*;

import java.util.UUID;

@Entity
public class Zeta {
    @Id
    @GeneratedValue
    private UUID id;
    private String zetaName;
    @Enumerated(EnumType.STRING)
    private ZetaStatus zetaStatus;

    public Zeta() { }

    public UUID getId() {
        return id;
    }

    public void setId(UUID id) {
        this.id = id;
    }

    public String getZetaName() {
        return zetaName;
    }

    public void setZetaName(String zetaName) {
        this.zetaName = zetaName;
    }

    public ZetaStatus getZetaStatus() {
        return zetaStatus;
    }

    public void setZetaStatus(ZetaStatus zetaStatus) {
        this.zetaStatus = zetaStatus;
    }
}

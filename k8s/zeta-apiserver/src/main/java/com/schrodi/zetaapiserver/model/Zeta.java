package com.schrodi.zetaapiserver.model;

import jakarta.persistence.*;

import java.util.UUID;

@Entity
public class Zeta {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;
    private String name;
    @Column(nullable = true)
    private String zipName;
    @Column(nullable = true)
    private String bucket;
    @Enumerated(EnumType.STRING)
    private ZetaStatus zetaStatus;

    public Zeta() { }

    public UUID getId() {
        return id;
    }

    public void setId(UUID id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public ZetaStatus getZetaStatus() {
        return zetaStatus;
    }

    public void setZetaStatus(ZetaStatus zetaStatus) {
        this.zetaStatus = zetaStatus;
    }

    public String getZipName() {
        return zipName;
    }

    public void setZipName(String zipName) {
        this.zipName = zipName;
    }

    public String getBucket() {
        return bucket;
    }

    public void setBucket(String bucket) {
        this.bucket = bucket;
    }
}

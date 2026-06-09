package com.schrodi.zeta_runner.dto;

public record ImageInfoResponse(
        String image,
        String imageTag,
        String registryUrl
) { }
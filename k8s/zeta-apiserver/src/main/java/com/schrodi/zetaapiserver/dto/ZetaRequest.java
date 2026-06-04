package com.schrodi.zetaapiserver.dto;

import org.springframework.web.multipart.MultipartFile;

public record ZetaRequest(
        MultipartFile file,
        String name
) { }

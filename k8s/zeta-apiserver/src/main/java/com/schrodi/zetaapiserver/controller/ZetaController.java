package com.schrodi.zetaapiserver.controller;

import com.schrodi.zetaapiserver.dto.ZetaRequest;
import com.schrodi.zetaapiserver.dto.ZetaResponse;
import com.schrodi.zetaapiserver.service.ZetaService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
public class ZetaController {
    private ZetaService zetaService;

    public ZetaController(ZetaService zetaService) {
        this.zetaService = zetaService;
    }

    @GetMapping("zeta/{name}")
    public ResponseEntity<ZetaResponse> getZeta(@PathVariable String name){
        return ResponseEntity.ok(zetaService.getZeta(name));
    }

    @PostMapping("zeta")
    public ResponseEntity<?> createZeta(
            @RequestParam("file") MultipartFile file,
            @RequestParam("name") String zetaName
    ) {
        return ResponseEntity.ok(
                zetaService.deployZeta(new ZetaRequest(file, zetaName))
        );
    }
}

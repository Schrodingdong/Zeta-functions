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

    @DeleteMapping("zeta/{id}")
    public ResponseEntity<Void> deleteZeta(@PathVariable String id){
        zetaService.deleteZeta(id);
        return ResponseEntity.noContent().build();
    }

    @GetMapping("zeta/{id}")
    public ResponseEntity<ZetaResponse> getZeta(@PathVariable String id){
        return ResponseEntity.ok(zetaService.getZeta(id));
    }

    @PostMapping("zeta")
    public ResponseEntity<ZetaResponse> createZeta(
            @RequestParam("file") MultipartFile file,
            @RequestParam("name") String zetaName
    ) {
        return ResponseEntity.ok(
                zetaService.deployZeta(new ZetaRequest(file, zetaName))
        );
    }
}

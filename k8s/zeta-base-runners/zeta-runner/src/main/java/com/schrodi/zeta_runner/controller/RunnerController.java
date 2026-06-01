package com.schrodi.zeta_runner.controller;

import com.schrodi.zeta_runner.dto.SpawnZetaRequest;
import com.schrodi.zeta_runner.service.RunnerService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;


@RestController
public class RunnerController {
    private final RunnerService runnerService;

    RunnerController(RunnerService runnerService) {
        this.runnerService = runnerService;
    }

    @GetMapping("runners")
    public String getAllRunners() {
        return new String();
    }

    @GetMapping("runners/{id}")
    public String getRunner(@PathVariable UUID id) {
        return new String();
    }

    @PostMapping("runners")
    public ResponseEntity<?> spawnRunner(@RequestBody SpawnZetaRequest spawnZetaRequest) {
        return ResponseEntity.ok(
                runnerService.spawnZeta(spawnZetaRequest.zetaName())
        );
    }
    
}

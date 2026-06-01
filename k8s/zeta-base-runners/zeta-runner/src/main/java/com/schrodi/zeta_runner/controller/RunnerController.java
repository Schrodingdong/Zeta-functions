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
    public ResponseEntity<?> getAllRunners() {
        return ResponseEntity.ok(
                runnerService.getZetaRunners()
        );
    }

    @GetMapping("runners/{zeta}")
    public ResponseEntity<?> getRunner(@PathVariable String zeta) {
        return ResponseEntity.ok(
            runnerService.getZetaRunner(zeta)
        );
    }

    @PostMapping("runners")
    public ResponseEntity<?> spawnRunner(@RequestBody SpawnZetaRequest spawnZetaRequest) {
        return ResponseEntity.ok(
                runnerService.spawnZeta(spawnZetaRequest.zetaName())
        );
    }

    @DeleteMapping("runners/{zeta}")
    public ResponseEntity<?> spawnRunner(@PathVariable String zeta) {
        runnerService.deleteZeta(zeta);
        return ResponseEntity.noContent().build();
    }

}

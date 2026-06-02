package com.schrodi.zeta_runner.controller;

import com.schrodi.zeta_runner.dto.ZetaRunnerRequest;
import com.schrodi.zeta_runner.service.RunnerService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;


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
        var a = runnerService.getZetaRunner(zeta);
        return ResponseEntity.ok(
            runnerService.getZetaRunner(zeta)
        );
    }

    @PostMapping("runners")
    public ResponseEntity<?> spawnRunner(@RequestBody ZetaRunnerRequest zetaRunnerRequest) {
        return ResponseEntity.ok(
                runnerService.spawnZeta(zetaRunnerRequest.zetaName())
        );
    }

    @DeleteMapping("runners/{zeta}")
    public ResponseEntity<?> deleteRunner(@PathVariable String zeta) {
        runnerService.deleteZetaRunner(zeta);
        return ResponseEntity.noContent().build();
    }

}

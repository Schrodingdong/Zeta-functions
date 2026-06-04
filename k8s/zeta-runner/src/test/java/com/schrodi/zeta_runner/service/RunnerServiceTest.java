package com.schrodi.zeta_runner.service;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import tools.jackson.databind.ObjectMapper;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest
class RunnerServiceTest {

    @Autowired
    private RunnerService runnerService;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void shouldSerializeRunner() throws Exception {
        var runner = runnerService.getZetaRunner("what");
        assertDoesNotThrow(() -> objectMapper.writeValueAsString(runner));
    }
}
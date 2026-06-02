package com.schrodi.zeta_runner.service;

import com.schrodi.zeta_runner.dto.ZetaProcessingStatusResponse;
import com.schrodi.zeta_runner.model.ZetaStatus;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.core.Message;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Service;
import tools.jackson.databind.ObjectMapper;

@Service
public class ZetaReceiver {
    private static final Logger log = LoggerFactory.getLogger(ZetaReceiver.class);
    private final RunnerService runnerService;
    private final ObjectMapper mapper;

    public ZetaReceiver(RunnerService runnerService, ObjectMapper mapper) {
        this.runnerService = runnerService;
        this.mapper = mapper;
    }

    @RabbitListener(queues = "${spring.rabbitmq.queues.deployment}")
    public String receiveDeploymentRequest(String zeta) {
        log.info("Received deployment request for zeta: {}", zeta);
        try {
            runnerService.spawnZeta(zeta);
        } catch (Exception e) {
            log.error("Error spawning zeta", e);
            return mapper.writeValueAsString(
                    new ZetaProcessingStatusResponse(ZetaStatus.ERROR, "Error spawning zeta: " + e.getMessage())
            );
        }
        return mapper.writeValueAsString(
                new ZetaProcessingStatusResponse(ZetaStatus.DEPLOYED, "Successfully deployed zeta: " + zeta )
        );
    }

    @RabbitListener(queues = "${spring.rabbitmq.queues.delete}")
    public String receiveDeleteRequest(Message msg) {
        String zeta = new String(msg.getBody());
        log.info("Receive delete request for zeta: {}", zeta);
        runnerService.deleteZetaRunner(zeta);
        return mapper.writeValueAsString(
                new ZetaProcessingStatusResponse(ZetaStatus.DELETED, "Successfully deleted zeta: " + zeta)
        );
    }
}

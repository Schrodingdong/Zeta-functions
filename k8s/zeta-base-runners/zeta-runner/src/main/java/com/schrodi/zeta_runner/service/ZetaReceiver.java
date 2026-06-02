package com.schrodi.zeta_runner.service;

import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Service;

@Service
public class ZetaReceiver {
    private final RunnerService runnerService;

    public ZetaReceiver(RunnerService runnerService) {
        this.runnerService = runnerService;
    }

    @RabbitListener(queues = "${spring.rabbitmq.queue}")
    public void receive(String zeta) {
        runnerService.spawnZeta(zeta);
    }
}

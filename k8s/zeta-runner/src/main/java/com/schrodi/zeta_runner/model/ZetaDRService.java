package com.schrodi.zeta_runner.model;

import io.kubernetes.client.openapi.models.V1Service;

import java.time.Instant;
import java.util.List;
import java.util.Map;

public record ZetaDRService(
        Metadata metadata,
        Spec spec
) {

    public record Metadata(
            Instant creationTimestamp,
            String name,
            String namespace
    ) {}

    public record Spec(
            String clusterIP,
            List<String> clusterIPs,
            List<String> externalIPs,
            List<Port> ports,
            Map<String, String> selector,
            String type
    ) {}

    public record Port(
            Integer nodePort,
            Integer port,
            String protocol,
            Integer targetPort
    ) {}

    public static ZetaDRService from(V1Service service) {
        return new ZetaDRService(
                new ZetaDRService.Metadata(
                        service.getMetadata().getCreationTimestamp().toInstant(),
                        service.getMetadata().getName(),
                        service.getMetadata().getNamespace()
                ),
                new ZetaDRService.Spec(
                        service.getSpec().getClusterIP(),
                        service.getSpec().getClusterIPs(),
                        service.getSpec().getExternalIPs(),
                        service.getSpec().getPorts()
                                .stream()
                                .map(p -> new ZetaDRService.Port(
                                        p.getNodePort(),
                                        p.getPort(),
                                        p.getProtocol(),
                                        p.getTargetPort() != null
                                                ? p.getTargetPort().getIntValue()
                                                : null
                                ))
                                .toList(),
                        service.getSpec().getSelector(),
                        service.getSpec().getType()
                )
        );
    }
}
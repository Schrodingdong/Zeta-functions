package com.schrodi.zeta_runner.model;

import io.kubernetes.client.openapi.models.V1Deployment;

import java.time.Instant;
import java.util.List;
import java.util.Map;

public record ZetaDRDeployment(
        Metadata metadata,
        Spec spec
) {

    public record Metadata(
            Instant creationTimestamp,
            String name,
            String namespace
    ) {}

    public record Spec(
            Integer replicas,
            Template template
    ) {}

    public record Template(
            TemplateMetadata metadata,
            TemplateSpec spec
    ) {}

    public record TemplateMetadata(
            Map<String, String> labels
    ) {}

    public record TemplateSpec(
            List<Container> containers
    ) {}

    public record Container(
            String name,
            String image,
            List<Port> ports
    ) {}

    public record Port(
            Integer containerPort,
            String protocol
    ) {}

    public static ZetaDRDeployment from(V1Deployment deployment) {
        return new ZetaDRDeployment(
                new ZetaDRDeployment.Metadata(
                        deployment.getMetadata().getCreationTimestamp().toInstant(),
                        deployment.getMetadata().getName(),
                        deployment.getMetadata().getNamespace()
                ),
                new ZetaDRDeployment.Spec(
                        deployment.getSpec().getReplicas(),
                        new ZetaDRDeployment.Template(
                                new ZetaDRDeployment.TemplateMetadata(
                                        deployment.getSpec()
                                                .getTemplate()
                                                .getMetadata()
                                                .getLabels()
                                ),
                                new ZetaDRDeployment.TemplateSpec(
                                        deployment.getSpec()
                                                .getTemplate()
                                                .getSpec()
                                                .getContainers()
                                                .stream()
                                                .map(c -> new ZetaDRDeployment.Container(
                                                        c.getName(),
                                                        c.getImage(),
                                                        c.getPorts()
                                                                .stream()
                                                                .map(p -> new ZetaDRDeployment.Port(
                                                                        p.getContainerPort(),
                                                                        p.getProtocol()
                                                                ))
                                                                .toList()
                                                ))
                                                .toList()
                                )
                        )
                )
        );
    }
}
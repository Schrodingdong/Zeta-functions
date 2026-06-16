package com.schrodi.zetaapiserver.service;

import com.schrodi.zetaapiserver.config.MinioConfig;
import com.schrodi.zetaapiserver.dto.ZetaProcessingStatusResponse;
import com.schrodi.zetaapiserver.exception.ZetaDeploymentException;
import com.schrodi.zetaapiserver.model.Zeta;
import com.schrodi.zetaapiserver.model.ZetaStatus;
import com.schrodi.zetaapiserver.repository.ZetaRepository;
import io.minio.MinioClient;
import io.minio.UploadObjectArgs;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.core.Queue;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;
import tools.jackson.databind.ObjectMapper;

import java.nio.file.Path;

@Component
public class ZetaDeploymentTask {
    private static final Logger log = LoggerFactory.getLogger(ZetaDeploymentTask.class);
    private final RabbitTemplate template;
    private final ObjectMapper mapper;
    private final Queue zetaDeploymentQueue;
    private final MinioConfig minioConfig;
    private final MinioClient minioClient;
    private final ZetaRepository zetaRepository;

    public ZetaDeploymentTask(
            RabbitTemplate template,
            ObjectMapper mapper,
            Queue zetaDeploymentQueue,
            MinioConfig minioConfig,
            MinioClient minioClient,
            ZetaRepository zetaRepository
    ) {
        this.template = template;
        this.mapper = mapper;
        this.zetaDeploymentQueue = zetaDeploymentQueue;
        this.minioConfig = minioConfig;
        this.minioClient = minioClient;
        this.zetaRepository = zetaRepository;
    }

    @Async
    public void deploy(Zeta zeta, Path tmpZipP) {
        log.info("Setting Zeta '{}:{}' status to DEPLOYING ", zeta.getName(), zeta.getId());
        zeta.setZetaStatus(ZetaStatus.DEPLOYING);
        zeta = zetaRepository.save(zeta);
        log.info("Set Zeta '{}:{}' status to DEPLOYING ", zeta.getName(), zeta.getId());

        log.info("Saving Zeta '{}:{}' ZIP to object storage ", zeta.getName(), zeta.getId());
        String zetaObject = zeta.getId() + ".zip";
        try {
            UploadObjectArgs uploadObjectArgs = UploadObjectArgs.builder()
                    .bucket(minioConfig.getBucket())
                    .object(zetaObject)
                    .filename(tmpZipP.toString())
                    .build();
            minioClient.uploadObject(uploadObjectArgs);
            log.info("Setting Zeta '{}:{}' zipName and bucket ", zeta.getName(), zeta.getId());
            zeta.setZipName(zetaObject);
            zeta.setBucket(minioConfig.getBucket());
            zeta = zetaRepository.save(zeta);
            log.info("Set Zeta '{}:{}' zipName and bucket ", zeta.getName(), zeta.getId());
        } catch (Exception e) {
            zeta.setZetaStatus(ZetaStatus.ERROR);
            zeta = zetaRepository.save(zeta);
            throw new ZetaDeploymentException(String.format("Unable to deploy Zeta '%s'", zeta.getId()), e);
        }
        log.info("Saved Zeta '{}:{}' ZIP to object storage ", zeta.getName(), zeta.getId());

        log.info("Deploying Zeta '{}:{}' DRs to cluster", zeta.getName(), zeta.getId());
        try {
            var zetaProcessingStatus = sendDeploymentRequest(zeta.getId().toString());
            if (zetaProcessingStatus.status() == ZetaStatus.ERROR) {
                throw new ZetaDeploymentException(String.format("Unable to deploy Zeta '%s'", zeta.getId()));
            }
        } catch (Exception e) {
            zeta.setZetaStatus(ZetaStatus.ERROR);
            zeta = zetaRepository.save(zeta);
            throw new ZetaDeploymentException(String.format("Unable to deploy Zeta '%s'", zeta.getId()));
        }
        log.info("Deployed Zeta '{}:{}' DRs to cluster", zeta.getName(), zeta.getId());

        log.info("Setting Zeta '{}:{}' status to DEPLOYED", zeta.getName(), zeta.getId());
        zeta.setZetaStatus(ZetaStatus.DEPLOYED);
        zeta = zetaRepository.save(zeta);
        log.info("Set Zeta '{}:{}' status to DEPLOYED", zeta.getName(), zeta.getId());
    }

    /**
     * Sends a deployment request to the zeta runner
     * @param id Zeta id
     * @return Zeta status post-deployment
     */
    private ZetaProcessingStatusResponse sendDeploymentRequest(String id) {
        var res = (String) template.convertSendAndReceive(zetaDeploymentQueue.getName(), id);
        return mapper.readValue(res, ZetaProcessingStatusResponse.class);
    }
}

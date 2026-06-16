package com.schrodi.zetaapiserver.service;

import com.schrodi.zetaapiserver.dto.ZetaProcessingStatusResponse;
import com.schrodi.zetaapiserver.exception.ZetaResourceNotFoundException;
import com.schrodi.zetaapiserver.model.Zeta;
import com.schrodi.zetaapiserver.model.ZetaStatus;
import com.schrodi.zetaapiserver.repository.ZetaRepository;
import io.minio.MinioClient;
import io.minio.RemoveObjectArgs;
import io.minio.errors.MinioException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.core.Queue;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;
import tools.jackson.databind.ObjectMapper;

@Component
public class ZetaDeleteRequest {
    private static final Logger log = LoggerFactory.getLogger(ZetaDeleteRequest.class);
    private final RabbitTemplate template;
    private final Queue zetaDeleteQueue;
    private final ObjectMapper mapper;
    private final MinioClient minioClient;
    private final ZetaRepository zetaRepository;

    public ZetaDeleteRequest(RabbitTemplate template, Queue zetaDeleteQueue, ObjectMapper mapper, MinioClient minioClient, ZetaRepository zetaRepository) {
        this.template = template;
        this.zetaDeleteQueue = zetaDeleteQueue;
        this.mapper = mapper;
        this.minioClient = minioClient;
        this.zetaRepository = zetaRepository;
    }

    @Async
    public void delete(Zeta zeta) {
        log.info("Setting Zeta '{}:{}' status to DELETING ", zeta.getName(), zeta.getId());
        zeta.setZetaStatus(ZetaStatus.DELETING);
        zetaRepository.save(zeta);
        log.info("Set Zeta '{}:{}' status to DELETING ", zeta.getName(), zeta.getId());

        log.info("Deleting DRs of Zeta '{}:{}'", zeta.getName(), zeta.getId());
        var statusRes = sendDeleteRequest(zeta.getId().toString());
        if(statusRes.status() == ZetaStatus.ERROR) {
            zeta.setZetaStatus(ZetaStatus.ERROR);
            zetaRepository.save(zeta);
            throw new RuntimeException(
                    String.format("Error deleting Zeta '%s' from cluster.", zeta.getId())
            );
        }
        log.info("Deleted DRs of Zeta '{}:{}'", zeta.getName(), zeta.getId());

        log.info("Deleting object storage assets of Zeta '{}:{}'", zeta.getName(), zeta.getId());
        try {
            deleteZetaObject(zeta);
        } catch (MinioException e) {
            zeta.setZetaStatus(ZetaStatus.ERROR);
            zetaRepository.save(zeta);
            throw new ZetaResourceNotFoundException(String.format(
                    "Unable to remove Zeta ZIP '%s' from MINIO", zeta.getZipName()
            ), e);
        }
        log.info("Deleted object storage assets of Zeta '{}:{}'", zeta.getName(), zeta.getId());

        log.info("Setting Zeta '{}:{}' status to DELETED", zeta.getName(), zeta.getId());
        try {
            zeta.setZetaStatus(ZetaStatus.DELETED);
            zetaRepository.save(zeta);
        } catch (Exception e) {
            throw new RuntimeException(String.format(
                    "Unable to set zeta '%s' status to DELETED", zeta.getId()
            ), e);
        }
        log.info("Set Zeta '{}:{}' status to DELETED", zeta.getName(), zeta.getId());
    }

    /**
     * Sends a delete request to the zeta runner
     * @param id Zeta id
     * @return Zeta status post-deletion
     */
    private ZetaProcessingStatusResponse sendDeleteRequest(String id) {
        var res = (String) template.convertSendAndReceive(zetaDeleteQueue.getName(), id);
        return mapper.readValue(res, ZetaProcessingStatusResponse.class);
    }

    /**
     * Delete Zeta ZIP from object storage
     * @param zeta
     * @throws MinioException
     */
    private void deleteZetaObject(Zeta zeta) throws MinioException {
        var removeObjectArgs = RemoveObjectArgs.builder()
                .bucket(zeta.getBucket())
                .object(zeta.getZipName())
                .build();
        minioClient.removeObject(removeObjectArgs);
    }
}

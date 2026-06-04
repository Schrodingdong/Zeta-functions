package com.schrodi.zetaapiserver.service;

import com.schrodi.zetaapiserver.config.MinioConfig;
import com.schrodi.zetaapiserver.dto.ZetaProcessingStatusResponse;
import com.schrodi.zetaapiserver.dto.ZetaRequest;
import com.schrodi.zetaapiserver.dto.ZetaResponse;
import com.schrodi.zetaapiserver.exception.ZetaDeploymentException;
import com.schrodi.zetaapiserver.exception.ZetaNotFoundException;
import com.schrodi.zetaapiserver.exception.ZetaResourceNotFoundException;
import com.schrodi.zetaapiserver.model.Zeta;
import com.schrodi.zetaapiserver.model.ZetaStatus;
import com.schrodi.zetaapiserver.repository.ZetaRepository;
import io.minio.MinioClient;
import io.minio.RemoveObjectArgs;
import io.minio.UploadObjectArgs;
import io.minio.errors.MinioException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.core.Queue;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.stereotype.Service;
import tools.jackson.databind.ObjectMapper;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.UUID;
import java.util.stream.StreamSupport;

@Service
public class ZetaService {
    private static final String PREFIX = "zeta-";
    private static final Logger log = LoggerFactory.getLogger(ZetaService.class);
    private final MinioClient minioClient;
    private final MinioConfig minioConfig;
    private final ZetaRepository zetaRepository;
    private final ObjectMapper mapper;

    private final RabbitTemplate template;
    private final Queue zetaDeploymentQueue;
    private final Queue zetaDeleteQueue;


    public ZetaService(
            ZetaRepository zetaRepository,
            MinioClient minioClient,
            MinioConfig minioConfig,
            ObjectMapper mapper,
            RabbitTemplate template,
            Queue zetaDeploymentQueue,
            Queue zetaDeleteQueue
    ) {
        this.minioClient = minioClient;
        this.minioConfig = minioConfig;
        this.zetaRepository = zetaRepository;
        this.mapper = mapper;
        this.template = template;
        this.zetaDeploymentQueue = zetaDeploymentQueue;
        this.zetaDeleteQueue = zetaDeleteQueue;
    }

    /**
     * Delete zeta
     */
    public void deleteZeta(String id) {
        Zeta zeta = zetaRepository.findById(UUID.fromString(id))
                .orElseThrow(() -> new ZetaNotFoundException(String.format("Zeta '%s' not found", id)));

        // Delete from cluster
        var zetaProcessingStatus = sendDeleteRequest(zeta.getId().toString());
        // Delete from ObjectStorage
        try {
            deleteZetaObject(zeta);
        } catch (MinioException e) {
            throw new ZetaResourceNotFoundException("Unable to remove ZIP from MINIO", e);
        }
        // Delete from RDBMS
        zeta.setZetaStatus(zetaProcessingStatus.status());
        zetaRepository.save(zeta);
    }

    /**
     * Retrieve All Zetas that aren't in DELETED status
     */
    public List<ZetaResponse> getAllZetas() {
        return zetaRepository.findByZetaStatusNot(ZetaStatus.DELETED)
                .stream()
                .map(ZetaResponse::new)
                .toList();
    }

    /**
     * Retrieve Zeta
     */
    public ZetaResponse getZeta(String id) {
        Zeta zeta = zetaRepository.findById(UUID.fromString(id))
                .orElseThrow(() -> new ZetaNotFoundException(String.format("Zeta '%s' not found", id)));
        return new ZetaResponse(zeta);
    }

    /**
     * Deploy a Zeta function
     * <p>
     * A deployment would mean:
     * <li>Saving metadata into RDBMS</li>
     * <li>Saving user's ZIP into ObjectStorage</li>
     * <li>Deploying k8s resources by the Zeta Runner</li>
     */
    public ZetaResponse deployZeta(ZetaRequest zetaRequest) {
        // Save in DB
        Zeta zeta = new Zeta();
        zeta.setName(zetaRequest.name());
        zeta.setZetaStatus(ZetaStatus.PENDING);
        zeta = zetaRepository.save(zeta);

        // Save the file in tmp
        String tmpDir = PREFIX + zeta.getId() + "_";
        Path tmpDirP;
        String tmpZip = zeta.getId() + "_";
        Path tmpZipP;
        try {
            tmpDirP = Files.createTempDirectory(tmpDir);
            tmpZipP = Files.createTempFile(tmpDirP, tmpZip, ".zip");
            byte[] zipContent = zetaRequest.file().getBytes();
            Files.write(tmpZipP, zipContent);
        } catch (IOException e) {
            throw new ZetaDeploymentException(String.format("Unable to deploy Zeta '%s'", zeta.getId()), e);
        }
        // Upload
        String zetaObject = zeta.getId() + ".zip";
        try {
            UploadObjectArgs uploadObjectArgs = UploadObjectArgs.builder()
                    .bucket(minioConfig.getBucket())
                    .object(zetaObject)
                    .filename(tmpZipP.toString())
                    .build();
            minioClient.uploadObject(uploadObjectArgs);
        } catch (Exception e) {
            throw new ZetaDeploymentException(String.format("Unable to deploy Zeta '%s'", zeta.getId()), e);
        }
        // Set Zeta Zip object name && Update status to deploying
        zeta.setZipName(zetaObject);
        zeta.setBucket(minioConfig.getBucket());
        zeta.setZetaStatus(ZetaStatus.DEPLOYING);
        zeta = zetaRepository.save(zeta);

        // Send deployment request to runner
        var zetaProcessingStatus = sendDeploymentRequest(zeta.getId().toString());
        if (zetaProcessingStatus.status() == ZetaStatus.ERROR) {
            // Undo minio
            try {
                deleteZetaObject(zeta);
            } catch (MinioException e) {
                throw new ZetaResourceNotFoundException(
                        String.format("Unable to remove ZIP for '%s' from MINIO", zeta.getId()),
                        e
                );
            }
            // Undo k8s
            sendDeleteRequest(zeta.getId().toString());
            throw new ZetaDeploymentException(String.format("Unable to deploy Zeta '%s'", zeta.getId()));
        }
        zeta.setZetaStatus(zetaProcessingStatus.status());
        zeta = zetaRepository.save(zeta);

        return new ZetaResponse(zeta);
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
     * Sends a deployment request to the zeta runner
     * @param id Zeta id
     * @return Zeta status post-deployment
     */
    private ZetaProcessingStatusResponse sendDeploymentRequest(String id) {
        var res = (String) template.convertSendAndReceive(zetaDeploymentQueue.getName(), id);
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

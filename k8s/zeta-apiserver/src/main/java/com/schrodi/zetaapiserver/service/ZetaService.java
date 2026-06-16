package com.schrodi.zetaapiserver.service;

import com.schrodi.zetaapiserver.dto.ZetaRequest;
import com.schrodi.zetaapiserver.dto.ZetaResponse;
import com.schrodi.zetaapiserver.exception.ZetaDeploymentException;
import com.schrodi.zetaapiserver.exception.ZetaNotFoundException;
import com.schrodi.zetaapiserver.model.Zeta;
import com.schrodi.zetaapiserver.model.ZetaStatus;
import com.schrodi.zetaapiserver.repository.ZetaRepository;
import org.jspecify.annotations.NonNull;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;
import java.util.stream.StreamSupport;

@Service
public class ZetaService {
    private static final Logger log = LoggerFactory.getLogger(ZetaService.class);
    private static final String PREFIX = "zeta-";
    private final ZetaRepository zetaRepository;
    private final ZetaDeploymentTask zetaDeploymentTask;
    private final ZetaDeleteRequest zetaDeleteRequest;


    public ZetaService(
            ZetaRepository zetaRepository,
            ZetaDeploymentTask zetaDeploymentTask,
            ZetaDeleteRequest zetaDeleteRequest
    ) {
        this.zetaRepository = zetaRepository;
        this.zetaDeploymentTask = zetaDeploymentTask;
        this.zetaDeleteRequest = zetaDeleteRequest;
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
        // Initialize zeta in DB
        Zeta zeta = new Zeta();
        zeta.setName(zetaRequest.name());
        zeta.setZetaStatus(ZetaStatus.PENDING);
        zeta = zetaRepository.save(zeta);
        ZetaResponse res = new ZetaResponse(zeta);

        // Save the file locally
        log.info("Saving Zeta '{}:{}' ZIP to tmp ", zeta.getName(), zeta.getId());
        Path tmpZipP;
        try {
            tmpZipP = saveFileToTmpZip(zeta, zetaRequest.file());
        } catch (IOException e) {
            throw new ZetaDeploymentException(String.format("Unable to deploy Zeta '%s'", zeta.getId()), e);
        }
        log.info("Saved Zeta '{}:{}' ZIP to tmp ", zeta.getName(), zeta.getId());

        // Async deployment
        zetaDeploymentTask.deploy(zeta, tmpZipP);
        return res;
    }

    /**
     * Retrieve All Zetas
     */
    public List<ZetaResponse> getAllZetas() {
        return StreamSupport.stream(zetaRepository.findAll().spliterator(), false)
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
     * Delete zeta
     */
    public void deleteZeta(String id) {
        Zeta zeta = zetaRepository.findById(UUID.fromString(id))
                .orElseThrow(() -> new ZetaNotFoundException(String.format("Zeta '%s' not found", id)));
        zetaDeleteRequest.delete(zeta);
    }

    private static @NonNull Path saveFileToTmpZip(Zeta zeta, MultipartFile file) throws IOException {
        Path tmpZipP;
        String tmpDirName = PREFIX + zeta.getId() + "_";
        Path tmpDirP = Files.createTempDirectory(tmpDirName);
        String tmpZipName = zeta.getId() + "_";
        tmpZipP = Files.createTempFile(tmpDirP, tmpZipName, ".zip");
        byte[] zipContent = file.getBytes();
        Files.write(tmpZipP, zipContent);
        return tmpZipP;
    }
}

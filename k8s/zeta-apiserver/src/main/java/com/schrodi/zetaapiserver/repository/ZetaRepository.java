package com.schrodi.zetaapiserver.repository;

import com.schrodi.zetaapiserver.model.Zeta;
import com.schrodi.zetaapiserver.model.ZetaStatus;
import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface ZetaRepository extends CrudRepository<Zeta, UUID> {
    Optional<Zeta> findByName(String name);
    List<Zeta> findByZetaStatusNot(ZetaStatus zetaStatus);
}

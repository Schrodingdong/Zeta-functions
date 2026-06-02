package com.schrodi.zetaapiserver.repository;

import com.schrodi.zetaapiserver.model.Zeta;
import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface ZetaRepository extends CrudRepository<Zeta, UUID> {
}

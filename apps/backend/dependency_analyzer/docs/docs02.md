## 完成系

```text
digraph dependencies {
  // Domain
  "domain.memo";

  // UseCases
  "usecases.add_memo";
  "usecases.create_memo";
  "usecases.incremental_vectorize";
  "usecases.search_memos";
  "usecases.list_tags";
  "usecases.list_categories";
  "usecases.get_progress";
  "usecases.rebuild_index";

  // Interfaces (DTOs, Repos, Utils)
  "interfaces.dtos.memo_dto";
  "interfaces.dtos.create_memo_dto";
  "interfaces.dtos.search_dto";
  "interfaces.repositories.memo_repo";
  "interfaces.repositories.index_repo";
  "interfaces.utils.datetime";
  "interfaces.controllers.common";
  "interfaces.controllers.memo_controller";
  "interfaces.controllers.admin_controller";

  // Infrastructure
  "infrastructure.persistence.fs_memo_repo";
  "infrastructure.persistence.faiss_index_repo";
  "infrastructure.utils.datetime_jst";
  "config";

  // → UseCases の依存
  "usecases.add_memo"          -> "domain.memo";
  "usecases.add_memo"          -> "interfaces.repositories.memo_repo";
  "usecases.add_memo"          -> "interfaces.utils.datetime";

  "usecases.create_memo"       -> "domain.memo";
  "usecases.create_memo"       -> "interfaces.repositories.memo_repo";
  "usecases.create_memo"       -> "interfaces.repositories.index_repo";
  "usecases.create_memo"       -> "interfaces.utils.datetime";

  "usecases.incremental_vectorize" -> "domain.memo";
  "usecases.incremental_vectorize" -> "interfaces.repositories.memo_repo";
  "usecases.incremental_vectorize" -> "interfaces.repositories.index_repo";

  "usecases.search_memos"      -> "domain.memo";

  "usecases.list_tags"         -> "interfaces.repositories.memo_repo";
  "usecases.list_categories"   -> "interfaces.repositories.memo_repo";

  "usecases.get_progress"      -> "interfaces.repositories.index_repo";

  "usecases.rebuild_index"     -> "domain.memo";
  "usecases.rebuild_index"     -> "interfaces.repositories.memo_repo";
  "usecases.rebuild_index"     -> "interfaces.repositories.index_repo";

  // → Controllers の依存
  "interfaces.controllers.common"         -> "interfaces.repositories.memo_repo";
  "interfaces.controllers.common"         -> "interfaces.repositories.index_repo";
  "interfaces.controllers.common"         -> "usecases.search_memos";
  "interfaces.controllers.common"         -> "usecases.create_memo";
  "interfaces.controllers.common"         -> "usecases.incremental_vectorize";
  "interfaces.controllers.common"         -> "usecases.get_progress";

  "interfaces.controllers.memo_controller" -> "interfaces.dtos.search_dto";
  "interfaces.controllers.memo_controller" -> "interfaces.dtos.create_memo_dto";
  "interfaces.controllers.memo_controller" -> "interfaces.dtos.memo_dto";
  "interfaces.controllers.memo_controller" -> "interfaces.controllers.common";
  "interfaces.controllers.memo_controller" -> "interfaces.repositories.memo_repo";
  "interfaces.controllers.memo_controller" -> "usecases.list_categories";
  "interfaces.controllers.memo_controller" -> "usecases.list_tags";
  "interfaces.controllers.memo_controller" -> "interfaces.utils.datetime";

  "interfaces.controllers.admin_controller" -> "interfaces.controllers.common";
  "interfaces.controllers.admin_controller" -> "usecases.incremental_vectorize";
  "interfaces.controllers.admin_controller" -> "usecases.get_progress";

  // → Infrastructure implements Interfaces
  "infrastructure.persistence.fs_memo_repo"   -> "interfaces.repositories.memo_repo";
  "infrastructure.persistence.faiss_index_repo" -> "interfaces.repositories.index_repo";
  "infrastructure.persistence.faiss_index_repo" -> "interfaces.repositories.memo_repo";

  "infrastructure.utils.datetime_jst"        -> "interfaces.utils.datetime";

  // → Config は最外層
  "interfaces.controllers.common"           -> "config";
  "interfaces.controllers.admin_controller" -> "config";
}
```

## 現状
```text
digraph dependencies {
    "main" -> "config";
    "main" -> "interfaces.controllers.memo_controller";
    "main" -> "interfaces.controllers.admin_controller";
    "main" -> "interfaces.controllers.common";
    "main" -> "infrastructure.persistence.fs_memo_repo";
    "main" -> "infrastructure.persistence.faiss_index_repo";
    "usecases.incremental_vectorize" -> "domain.memo";
    "usecases.incremental_vectorize" -> "interfaces.repositories.memo_repo";
    "usecases.incremental_vectorize" -> "interfaces.repositories.index_repo";
    "usecases.add_memo" -> "domain.memo";
    "usecases.add_memo" -> "interfaces.repositories.memo_repo";
    "usecases.add_memo" -> "infrastructure.utils.datetime_jst";
    "usecases.create_memo" -> "domain.memo";
    "usecases.create_memo" -> "interfaces.repositories.memo_repo";
    "usecases.create_memo" -> "infrastructure.utils.datetime_jst";
    "usecases.create_memo" -> "interfaces.repositories.index_repo";
    "usecases.search_memos" -> "domain.memo";
    "usecases.list_tags" -> "interfaces.repositories.memo_repo";
    "usecases.list_categories" -> "interfaces.repositories.memo_repo";
    "usecases.rebuild_index" -> "interfaces.repositories.index_repo";
    "usecases.rebuild_index" -> "interfaces.repositories.memo_repo";
    "usecases.rebuild_index" -> "domain.memo";
    "interfaces.repositories.memo_repo" -> "domain.memo";
    "interfaces.repositories.index_repo" -> "domain.memo";
    "interfaces.dtos.memo_dto" -> "domain.memo";
    "interfaces.dtos.search_dto" -> "domain.memo";
    "interfaces.controllers.admin_controller" -> "interfaces.controllers.common";
    "interfaces.controllers.admin_controller" -> "usecases.incremental_vectorize";
    "interfaces.controllers.admin_controller" -> "usecases.get_progress";
    "interfaces.controllers.common" -> "config";
    "interfaces.controllers.common" -> "interfaces.repositories.memo_repo";
    "interfaces.controllers.common" -> "interfaces.repositories.index_repo";
    "interfaces.controllers.common" -> "usecases.search_memos";
    "interfaces.controllers.common" -> "usecases.create_memo";
    "interfaces.controllers.common" -> "usecases.incremental_vectorize";
    "interfaces.controllers.common" -> "usecases.get_progress";
    "interfaces.controllers.memo_controller" -> "interfaces.dtos.search_dto";
    "interfaces.controllers.memo_controller" -> "interfaces.dtos.create_memo_dto";
    "interfaces.controllers.memo_controller" -> "interfaces.dtos.memo_dto";
    "interfaces.controllers.memo_controller" -> "interfaces.controllers.common";
    "interfaces.controllers.memo_controller" -> "infrastructure.utils.datetime_jst";
    "interfaces.controllers.memo_controller" -> "interfaces.repositories.memo_repo";
    "interfaces.controllers.memo_controller" -> "infrastructure.persistence.fs_memo_repo";
    "interfaces.controllers.memo_controller" -> "usecases.list_categories";
    "interfaces.controllers.memo_controller" -> "usecases.list_tags";
    "infrastructure.persistence.faiss_index_repo" -> "domain.memo";
    "infrastructure.persistence.faiss_index_repo" -> "interfaces.repositories.index_repo";
    "infrastructure.persistence.faiss_index_repo" -> "interfaces.repositories.memo_repo";
    "infrastructure.persistence.fs_memo_repo" -> "domain.memo";
    "infrastructure.persistence.fs_memo_repo" -> "interfaces.repositories.memo_repo";
    "infrastructure.persistence.fs_memo_repo" -> "infrastructure.utils.datetime_jst";
}
```

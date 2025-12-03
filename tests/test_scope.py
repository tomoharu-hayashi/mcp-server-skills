"""スコープ機能のテスト"""

from pathlib import Path

from mcp_brain.models import Knowledge
from mcp_brain.storage import (
    GLOBAL_SCOPE,
    KnowledgeStorage,
    get_scope_hierarchy,
    path_to_scope,
)


class TestScopeHierarchy:
    """スコープ階層の生成テスト"""

    def test_global_only(self):
        """プロジェクトパスがNoneの場合はglobalのみ"""
        hierarchy = get_scope_hierarchy(None)
        assert hierarchy == [GLOBAL_SCOPE]

    def test_single_level(self, tmp_path):
        """1階層のプロジェクト"""
        project = tmp_path / "project"
        project.mkdir()
        hierarchy = get_scope_hierarchy(project)

        # 最後は必ずglobal
        assert hierarchy[-1] == GLOBAL_SCOPE
        # 最初はプロジェクト自身
        assert hierarchy[0] == path_to_scope(project)

    def test_multi_level(self, tmp_path):
        """複数階層のプロジェクト"""
        project = tmp_path / "pj" / "my" / "app"
        project.mkdir(parents=True)
        hierarchy = get_scope_hierarchy(project)

        # プロジェクト → 親 → ... → global の順
        assert hierarchy[-1] == GLOBAL_SCOPE
        assert path_to_scope(project) in hierarchy[0]
        assert path_to_scope(project.parent) in hierarchy
        assert path_to_scope(project.parent.parent) in hierarchy

    def test_sibling_excluded(self, tmp_path):
        """兄弟ディレクトリは含まれない"""
        parent = tmp_path / "projects"
        parent.mkdir()
        project_a = parent / "app-a"
        project_b = parent / "app-b"
        project_a.mkdir()
        project_b.mkdir()

        hierarchy_a = get_scope_hierarchy(project_a)
        hierarchy_b = get_scope_hierarchy(project_b)

        # app-a の階層に app-b は含まれない
        assert path_to_scope(project_b) not in hierarchy_a
        # app-b の階層に app-a は含まれない
        assert path_to_scope(project_a) not in hierarchy_b
        # 両方とも親は含まれる
        assert path_to_scope(parent) in hierarchy_a
        assert path_to_scope(parent) in hierarchy_b


class TestScopePriority:
    """スコープ優先度のテスト"""

    def test_project_overrides_global(self, tmp_path):
        """プロジェクト固有の知識がglobalより優先される"""
        storage = KnowledgeStorage(tmp_path / "knowledge")
        project = tmp_path / "my-project"
        project.mkdir()
        storage.set_project(project)

        # globalスコープに知識を保存
        global_knowledge = Knowledge(
            name="deploy", description="Global deployment", content="## Global steps"
        )
        storage.save(global_knowledge, scope=GLOBAL_SCOPE)

        # プロジェクトスコープに同名の知識を保存
        project_knowledge = Knowledge(
            name="deploy",
            description="Project-specific deployment",
            content="## Project steps",
        )
        project_scope = storage.save(project_knowledge)

        # load() はプロジェクト固有を返す
        loaded = storage.load("deploy")
        assert loaded is not None
        assert loaded.description == "Project-specific deployment"

        # list_all() でも重複除去されプロジェクト固有のみ
        items = storage.list_all()
        deploy_items = [k for k in items if k.name == "deploy"]
        assert len(deploy_items) == 1
        assert deploy_items[0].description == "Project-specific deployment"

    def test_parent_overrides_global(self, tmp_path):
        """親ディレクトリの知識がglobalより優先される"""
        storage = KnowledgeStorage(tmp_path / "knowledge")
        parent = tmp_path / "pj"
        project = parent / "my-app"
        parent.mkdir()
        project.mkdir()
        storage.set_project(project)

        # globalスコープに知識を保存
        global_knowledge = Knowledge(
            name="test-command", description="Global test", content="## Global"
        )
        storage.save(global_knowledge, scope=GLOBAL_SCOPE)

        # 親スコープに同名の知識を保存
        parent_knowledge = Knowledge(
            name="test-command", description="Parent test", content="## Parent"
        )
        parent_scope = path_to_scope(parent)
        storage.save(parent_knowledge, scope=parent_scope)

        # load() は親スコープを返す
        loaded = storage.load("test-command")
        assert loaded is not None
        assert loaded.description == "Parent test"

    def test_three_level_priority(self, tmp_path):
        """3階層の優先度テスト"""
        storage = KnowledgeStorage(tmp_path / "knowledge")
        grandparent = tmp_path / "workspace"
        parent = grandparent / "projects"
        project = parent / "app"
        grandparent.mkdir()
        parent.mkdir()
        project.mkdir()
        storage.set_project(project)

        # 3つのスコープに同名の知識を保存
        storage.save(
            Knowledge(name="config", description="Global", content="# Global"),
            scope=GLOBAL_SCOPE,
        )
        storage.save(
            Knowledge(
                name="config", description="Grandparent", content="# Grandparent"
            ),
            scope=path_to_scope(grandparent),
        )
        storage.save(
            Knowledge(name="config", description="Parent", content="# Parent"),
            scope=path_to_scope(parent),
        )
        storage.save(
            Knowledge(name="config", description="Project", content="# Project"),
            scope=path_to_scope(project),
        )

        # 最も具体的なプロジェクトスコープが優先
        loaded = storage.load("config")
        assert loaded is not None
        assert loaded.description == "Project"

        # list_all() でも1つだけ
        items = storage.list_all()
        config_items = [k for k in items if k.name == "config"]
        assert len(config_items) == 1
        assert config_items[0].description == "Project"


class TestScopeIsolation:
    """スコープの分離テスト"""

    def test_sibling_projects_isolated(self, tmp_path):
        """兄弟プロジェクトは互いに見えない"""
        base = tmp_path / "knowledge"
        project_a = tmp_path / "project-a"
        project_b = tmp_path / "project-b"
        project_a.mkdir()
        project_b.mkdir()

        # プロジェクトAの知識を作成
        storage_a = KnowledgeStorage(base, project_path=project_a)
        storage_a.save(Knowledge(name="app-a-config", description="Config for A"))

        # プロジェクトBから見えない
        storage_b = KnowledgeStorage(base, project_path=project_b)
        items_b = storage_b.list_all()
        names_b = {k.name for k in items_b}
        assert "app-a-config" not in names_b

        # プロジェクトBの知識を作成
        storage_b.save(Knowledge(name="app-b-config", description="Config for B"))

        # プロジェクトAから見えない
        items_a = storage_a.list_all()
        names_a = {k.name for k in items_a}
        assert "app-b-config" not in names_a

    def test_global_visible_from_all(self, tmp_path):
        """globalは全プロジェクトから見える"""
        base = tmp_path / "knowledge"
        project_a = tmp_path / "project-a"
        project_b = tmp_path / "project-b"
        project_a.mkdir()
        project_b.mkdir()

        # globalに知識を作成
        storage_global = KnowledgeStorage(base)
        storage_global.save(Knowledge(name="shared-tool", description="Shared"))

        # プロジェクトAから見える
        storage_a = KnowledgeStorage(base, project_path=project_a)
        items_a = storage_a.list_all()
        names_a = {k.name for k in items_a}
        assert "shared-tool" in names_a

        # プロジェクトBからも見える
        storage_b = KnowledgeStorage(base, project_path=project_b)
        items_b = storage_b.list_all()
        names_b = {k.name for k in items_b}
        assert "shared-tool" in names_b

    def test_list_current_scope_only(self, tmp_path):
        """list_current_scope()は現在のスコープのみ"""
        storage = KnowledgeStorage(tmp_path / "knowledge")
        parent = tmp_path / "parent"
        project = parent / "project"
        parent.mkdir()
        project.mkdir()
        storage.set_project(project)

        # 異なるスコープに知識を保存
        storage.save(
            Knowledge(name="global-item", description="Global"), scope=GLOBAL_SCOPE
        )
        storage.save(
            Knowledge(name="parent-item", description="Parent"),
            scope=path_to_scope(parent),
        )
        storage.save(
            Knowledge(name="project-item", description="Project"),
            scope=path_to_scope(project),
        )

        # list_all() は全て取得
        all_items = storage.list_all()
        all_names = {k.name for k in all_items}
        assert all_names == {"global-item", "parent-item", "project-item"}

        # list_current_scope() はプロジェクトのみ
        current_items = storage.list_current_scope()
        current_names = {k.name for k in current_items}
        assert current_names == {"project-item"}

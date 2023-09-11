import os
from datetime import date
from typing import List

from starlette.requests import Request

from dashboard import enums
from last.services import enums as _enums
from dashboard.constants import BASE_DIR
from dashboard.models import Admin, Cat, Category, Config, Dog1, Evaluation, LabelPage, Log
from dashboard.models import Permission as PermissionModel
from dashboard.models import Product
from dashboard.models import Resource as ResourceModel
from dashboard.models import Role as RoleModel
from dashboard.models import Sponsor
from dashboard.models import Evaluation
from dashboard.models import EvaluationPlanManager
from dashboard.models import EvaluationDatasetManager
from dashboard.providers import import_export_provider
from dashboard.widgets.displays import ShowIp
from last.services.app import app
from last.services.enums import Method
from last.services.file_upload import FileUpload
from last.services.i18n import _
from last.services.resources import (
    Action,
    ComputeField,
    Dropdown,
    Field,
    Link,
    Model,
    ToolbarAction,
)
from last.services.widgets import displays, filters, inputs

upload = FileUpload(uploads_dir=os.path.join(BASE_DIR, "static", "uploads"))


@app.register
class Dashboard(Link):
    label = "Dashboard"
    icon = "fas fa-home"
    url = "/admin"


@app.register
class Notification(Link):
    label = "Notification"
    icon = "far fa-bell"
    url = "/admin/notification"


@app.register
class Label(Link):
    label = "Label"
    icon = "fas fa-tag"
    url = "/admin/label"


@app.register
class Evaluation(Model):
    label: str = "Evaluation"
    icon = "fas fa-user"
    model = Evaluation
    filters = [
        filters.Search(
            name="username",
            label="Username",
            search_mode="contains",
            placeholder="评测模型/版本/方案",
        ),
    ]


@app.register
class Content(Dropdown):
    class CategoryResource(Model):
        label = "Category"
        model = Category
        filters = [filters.Search(name="name", label="Name")]
        fields = ["id", "name", "slug", "created_at"]

        async def get_toolbar_actions(self, request: Request) -> List[ToolbarAction]:
            actions = await super().get_toolbar_actions(request)
            actions.append(import_export_provider.import_action)
            actions.append(import_export_provider.export_action)
            return actions

    class ProductResource(Model):
        label = "Product"
        model = Product
        filters = [
            filters.Enum(enum=enums.ProductType, name="type", label="ProductType"),
            filters.Datetime(name="created_at", label="CreatedAt"),
        ]
        fields = [
            "id",
            "name",
            "view_num",
            "sort",
            "is_reviewed",
            "type",
            Field(name="image", label="Image", display=displays.Image(width="40")),
            Field(name="body", label="Body", input_=inputs.Editor()),
            "created_at",
        ]

    label = "Content"
    icon = "fas fa-bars"
    resources = [ProductResource, CategoryResource]


@app.register
class ConfigResource(Model):
    label = "Config"
    model = Config
    icon = "fas fa-cogs"
    filters = [
        filters.Enum(
            enum=enums.Status,
            name="status",
            label="Status",
        ),
        filters.Search(name="key", label="Key", search_mode="equal"),
    ]
    fields = [
        "id",
        "label",
        "key",
        "value",
        Field(
            name="status",
            label="Status",
            input_=inputs.RadioEnum(enums.Status, default=enums.Status.on),
        ),
    ]

    async def row_attributes(self, request: Request, obj: dict) -> dict:
        if obj.get("status") == enums.Status.on:
            return {"class": "bg-green text-white"}
        return await super().row_attributes(request, obj)

    async def get_actions(self, request: Request) -> List[Action]:
        actions = await super().get_actions(request)
        switch_status = Action(
            label="Switch Status",
            icon="ti ti-toggle-left",
            name="switch_status",
            method=Method.PUT,
        )
        actions.append(switch_status)
        return actions


@app.register
class LogResource(Model):
    label = "Log"
    model = Log
    icon = "far fa-sticky-note"
    fields = [
        "id",
        "admin",
        Field(name="ip", label="IP", display=ShowIp()),
        "resource",
        "content",
        "action",
        "created_at",
    ]
    filters = [
        filters.ForeignKey(
            name="admin",
            label="Admin",
            model=Admin,
        ),
        filters.DistinctColumn(
            Log,
            name="action",
            label="Action",
        ),
        filters.Date(name="created_at", label="CreatedAt"),
    ]

    async def get_toolbar_actions(self, request: Request) -> List[Action]:
        return []

    async def column_attributes(self, request: Request, field: Field) -> dict:
        if field.name == "content":
            return {"width": "40%"}
        return await super().column_attributes(request, field)

    async def cell_attributes(self, request: Request, obj: dict, field: Field) -> dict:
        if field.name == "id":
            return {"class": "bg-danger text-white"}
        return await super().cell_attributes(request, obj, field)

    async def get_actions(self, request: Request) -> List[Action]:
        return []

    async def get_bulk_actions(self, request: Request) -> List[Action]:
        return []


@app.register
class Auth(Dropdown):
    class AdminResource(Model):
        label = "Admin"
        model = Admin
        icon = "fas fa-user"
        page_pre_title = "admin list"
        page_title = "Admin Model"
        filters = [
            filters.Search(
                name="username",
                label="Name",
                search_mode="contains",
                placeholder="Search for username",
            ),
            filters.Date(name="created_at", label="CreatedAt", placeholder="Filter by created_at"),
            filters.Boolean(name="is_active", label="IsActive"),
        ]
        fields = [
            "id",
            "username",
            "channel",
            Field(
                name="password",
                label="Password",
                display=displays.InputOnly(),
                input_=inputs.Password(help_text="Password will auto hash when changed"),
            ),
            Field(name="email", label="Email", input_=inputs.Email()),
            Field(
                name="avatar",
                label="Avatar",
                display=displays.Image(width="40"),
                input_=inputs.Image(null=True, upload=upload),
            ),
            "last_login",
            "is_superuser",
            "is_active",
            "created_at",
        ]

    class Resource(Model):
        label = "Resource"
        model = ResourceModel

        async def get_actions(self, request: Request) -> List[Action]:
            return []

        async def get_bulk_actions(self, request: Request) -> List[Action]:
            return []

    class Permission(Model):
        label = "Permission"
        model = PermissionModel

        async def get_actions(self, request: Request) -> List[Action]:
            return []

        async def get_bulk_actions(self, request: Request) -> List[Action]:
            return []

    class Role(Model):
        label = "Role"
        model = RoleModel

    label = "Auth"
    icon = "fas fa-users"
    resources = [AdminResource, Resource, Permission, Role]


class SponsorUsernameDisplay(displays.Display):
    template = "sponsor_username.html"


class RestDays(ComputeField):
    async def get_value(self, request: Request, obj: dict):
        v = await super(RestDays, self).get_value(request, obj)
        days = (v - date.today()).days
        return days if days >= 0 else 0


class Amount(ComputeField):
    async def get_value(self, request: Request, obj: dict):
        v = await super(Amount, self).get_value(request, obj)
        return f'{obj.get("currency")}{v}'


@app.register
class SponsorResource(Model):
    label = "Sponsor"
    model = Sponsor
    page_pre_title = "Sponsor"
    page_title = "Thanks for all the sponsors!"
    icon = "far fa-heart"
    filters = ["username", filters.Date("sponsor_date", label="Sponsor Date")]
    fields = [
        "id",
        Field(name="username", label="username", display=SponsorUsernameDisplay()),
        "sponsor_date",
        Field(name="amount", display=displays.InputOnly()),
        Field(name="currency", display=displays.InputOnly()),
        Amount(name="amount", label="Amount"),
    ]

    async def get_actions(self, request: Request) -> List[Action]:
        return [
            Action(
                label=_("update"),
                icon="ti ti-edit",
                name="update",
                method=Method.GET,
                ajax=False,
            ),
        ]

    async def get_bulk_actions(self, request: Request) -> List[Action]:
        return []


@app.register
class GithubLink(Link):
    label = "Github"
    url = "https://github.com/fastapi-admin/fastapi-admin"
    icon = "fab fa-github"
    target = "_blank"


@app.register
class DocumentationLink(Link):
    label = "Documentation"
    url = "https://fastapi-admin-docs.long2ice.io"
    icon = "fas fa-file-code"
    target = "_blank"


@app.register
class SwitchLayout(Link):
    label = "Switch Layout"
    url = "/admin/layout"
    icon = "fas fa-grip-horizontal"


@app.register
class SimpleTable(Link):
    label = "Simple Table1"
    icon = "fa-solid fa-table"
    url = "/admin/stable1"


@app.register
class Animal(Dropdown):
    class CatResource(Model):
        label = "Cat"
        model = Cat
        filters = [filters.Search(name="name", label="Name")]
        fields = ["id", "name", "age", "birth_at"]

    class DogResource(Model):
        label = "Dog"
        model = Dog1
        filters = [
            filters.Enum(enum=enums.GenderType, name="gender", label="Gender"),
            filters.Datetime(name="birth_at", label="Birth_At"),
        ]
        fields = [
            "id",
            "name",
            "age",
            "gender",
            Field(
                name="image",
                label="Image",
                display=displays.Image(width="40"),
                input_=inputs.Image(null=True, upload=upload),
            ),
            "birth_at",
        ]

    label = "Animal"
    icon = "fas fa-bars"
    resources = [CatResource, DogResource]

@app.register
class DataManager(Dropdown):
    class EvaluationPlanManagerResource(Model):
        label = "评测方案管理"
        model = EvaluationPlanManager
        filters = [filters.Search(name="name", label="方案名称")]
        fields = ["id",
                  Field(name="plan_name", label="评测方案"),
                  Field(name="plan_content", label="风险类型/数据占比/评测权重")]

        async def get_actions(self, request: Request) -> List[Action]:
            return [
                Action(
                    label=_("update"),
                    icon="ti ti-edit",
                    name="update",
                    method=_enums.Method.GET,
                    ajax=False,
                ),
                Action(
                    label="Copy Create",
                    icon="ti ti-toggle-left",
                    name="copy_create",
                    method=_enums.Method.GET,
                ),
                Action(
                    label=_("delete"),
                    icon="ti ti-trash",
                    name="delete",
                    method=_enums.Method.DELETE,
                ),
            ]

        async def get_toolbar_actions(self, request: Request) -> List[ToolbarAction]:
            return [
                ToolbarAction(
                    label=_("新建方案"),
                    icon="fas fa-plus",
                    name="create",
                    method=_enums.Method.GET,
                    ajax=False,
                    class_="btn-dark",
                )
            ]

    class EvaluationDatasetManagerResource(Model):
        label = "评测集管理"
        model = EvaluationDatasetManager
        page_title = "评测集管理"
        filters = [filters.Search(name="name", label="评测集名称"),
                   filters.Search(name="type", label="风险类型")]
        fields = ["id",
                  Field(name="name", label="评测集名称"),
                  Field(name="type", label="风险类型"),
                  Field(name="sub_type", label="二级类型"),
                  Field(name="updateTime", label="更新时间"),
                  Field(name="useCount", label="使用次数")
                  ]

        async def get_toolbar_actions(self, request: Request) -> List[ToolbarAction]:
            return [
                ToolbarAction(
                    label=_("上传数据集"),
                    icon="fas fa-upload",
                    name="upload_dataset",
                    method=_enums.Method.GET,
                    ajax=False,
                    class_="btn-primary",
                )
            ]

        async def get_actions(self, request: Request) -> List[Action]:
            return [
                Action(
                    label=_("详细信息"),
                    icon="ti ti-edit",
                    name="update",
                    method=_enums.Method.GET,
                    ajax=False,
                ),
                Action(
                    label=_("导出"),
                    icon="ti ti-edit",
                    name="update",
                    method=_enums.Method.GET,
                    ajax=False,
                ),
                Action(
                    label=_("删除"),
                    icon="ti ti-trash",
                    name="delete",
                    method=_enums.Method.DELETE,
                )
            ]

    label = "数据管理"
    icon = "fas fa-bars"
    resources = [EvaluationDatasetManagerResource, EvaluationPlanManagerResource]

class DataManagePage(Dropdown):
    class LabelingPage(Model):
        label = "Labeling"
        model = LabelPage
        filters = [filters.Search(name="task_type", label="Task Type")]
        fields = ["id", "task_type", "labeling_method", "release_time", "current_status"]

    label = "DataSet"
    icon = "fas fa-bars"
    resources = [LabelingPage]


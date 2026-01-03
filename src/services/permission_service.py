"""
权限服务
管理用户菜单和操作权限
"""
from typing import List, Dict, Any, Optional


class PermissionService:
    """权限服务类"""
    
    # 定义所有菜单和路由配置（基于前端路由结构）
    ALL_MENUS = [
        {
            "path": "/",
            "alias": ["/login"],
            "name": "login",
            "component": "@/pages/login/index.vue",
            "meta": {
                "requiresAuth": False,
                "title": "登录",
                "icon": None,
                "hidden": False
            },
            "children": []
        },
        {
            "path": "/unauthorized",
            "name": "unauthorized",
            "component": "@/pages/unauthorized/index.vue",
            "meta": {
                "requiresAuth": False,
                "title": "未授权",
                "icon": None,
                "hidden": True
            },
            "children": []
        },
        {
            "path": "/a",
            "name": "login1",
            "component": "@/pages/login/index1.vue",
            "meta": {
                "requiresAuth": False,
                "title": "登录页1",
                "icon": None,
                "hidden": True
            },
            "children": []
        },
        {
            "path": "/second",
            "name": "second",
            "component": "@/pages/second/index.vue",
            "meta": {
                "requiresAuth": True,
                "title": "主页面",
                "icon": "home",
                "hidden": False
            },
            "children": [
                {
                    "path": "test",
                    "name": "test",
                    "component": "@/pages/test/index.vue",
                    "meta": {
                        "requiresAuth": True,
                        "title": "测试页",
                        "icon": "test",
                        "hidden": False
                    },
                    "permissions": ["test:view"]  # 需要的操作权限
                },
                {
                    "path": "originalQuestionBank",
                    "name": "originalQuestionBank",
                    "component": "@/pages/originalQuestionBank/index.vue",
                    "meta": {
                        "requiresAuth": True,
                        "title": "原题库",
                        "icon": "book",
                        "hidden": False
                    },
                    "permissions": ["questionBank:view"]
                },
                {
                    "path": "cleaningWarehouse",
                    "name": "CleaningWarehouse",
                    "component": "@/pages/cleaningWarehouse/index.vue",
                    "meta": {
                        "requiresAuth": True,
                        "title": "清洗库",
                        "icon": "warehouse",
                        "hidden": False
                    },
                    "permissions": ["cleaningWarehouse:view"]
                },
                {
                    "path": "examinationPaper",
                    "name": "examinationPaper",
                    "component": "@/pages/examinationPaper/index.vue",
                    "meta": {
                        "requiresAuth": True,
                        "title": "试卷",
                        "icon": "file",
                        "hidden": False
                    },
                    "permissions": ["examinationPaper:view"]
                },
                {
                    "path": "questionBankDetail/:id",
                    "name": "questionBankDetail",
                    "component": "@/pages/originalQuestionBank/detail/index.vue",
                    "props": True,
                    "meta": {
                        "requiresAuth": True,
                        "title": "题库详情",
                        "icon": None,
                        "hidden": True  # 详情页通常在菜单中隐藏
                    },
                    "permissions": ["questionBank:view", "questionBank:detail"]
                },
                {
                    "path": "questionTypeDetail/:bankId/:type",
                    "name": "questionTypeDetail",
                    "component": "@/pages/originalQuestionBank/questionType/index.vue",
                    "props": True,
                    "meta": {
                        "requiresAuth": True,
                        "title": "题目类型",
                        "icon": None,
                        "hidden": True
                    },
                    "permissions": ["questionBank:view", "questionBank:type"]
                }
            ]
        },
        {
            "path": "/:pathMatch(.*)*",
            "name": "not-found",
            "component": "@/pages/404/index.vue",
            "meta": {
                "requiresAuth": False,
                "title": "404",
                "icon": None,
                "hidden": True
            },
            "children": []
        }
    ]
    
    # 定义所有操作权限
    ALL_PERMISSIONS = [
        # 测试页权限
        "test:view",
        "test:create",
        "test:edit",
        "test:delete",
        
        # 题库权限
        "questionBank:view",
        "questionBank:create",
        "questionBank:edit",
        "questionBank:delete",
        "questionBank:detail",
        "questionBank:type",
        "questionBank:import",
        "questionBank:export",
        
        # 清洗库权限
        "cleaningWarehouse:view",
        "cleaningWarehouse:create",
        "cleaningWarehouse:edit",
        "cleaningWarehouse:delete",
        "cleaningWarehouse:process",
        "cleaningWarehouse:export",
        
        # 试卷权限
        "examinationPaper:view",
        "examinationPaper:create",
        "examinationPaper:edit",
        "examinationPaper:delete",
        "examinationPaper:export",
        "examinationPaper:publish",
    ]
    
    # 角色权限配置（每个角色拥有的权限）
    ROLE_PERMISSIONS = {
        'super_admin': [
            # 超级管理员拥有所有权限
            "*"  # 通配符表示所有权限
        ],
        'admin': [
            # 管理员权限
            "test:view",
            "test:create",
            "test:edit",
            "test:delete",
            "questionBank:view",
            "questionBank:create",
            "questionBank:edit",
            "questionBank:delete",
            "questionBank:detail",
            "questionBank:type",
            "questionBank:import",
            "questionBank:export",
            "cleaningWarehouse:view",
            "cleaningWarehouse:create",
            "cleaningWarehouse:edit",
            "cleaningWarehouse:delete",
            "cleaningWarehouse:process",
            "cleaningWarehouse:export",
            "examinationPaper:view",
            "examinationPaper:create",
            "examinationPaper:edit",
            "examinationPaper:delete",
            "examinationPaper:export",
            "examinationPaper:publish",
        ],
        'user': [
            # 普通用户权限（只读）
            "test:view",
            "questionBank:view",
            "questionBank:detail",
            "questionBank:type",
            "cleaningWarehouse:view",
            "examinationPaper:view",
        ]
    }
    
    # 角色可访问的菜单（基于requiresAuth和权限）
    ROLE_MENUS = {
        'super_admin': ['*'],  # 所有菜单
        'admin': ['*'],  # 所有菜单
        'user': ['*']  # 所有菜单（但操作权限受限）
    }
    
    @staticmethod
    def has_permission(user_role: str, permission: str) -> bool:
        """
        检查用户角色是否拥有指定权限
        :param user_role: 用户角色
        :param permission: 权限标识
        :return: 是否拥有权限
        """
        if not user_role or not permission:
            return False
        
        role_perms = PermissionService.ROLE_PERMISSIONS.get(user_role, [])
        
        # 检查通配符权限（超级管理员）
        if '*' in role_perms:
            return True
        
        # 检查精确权限
        if permission in role_perms:
            return True
        
        # 检查通配符匹配（例如 questionBank:* 匹配所有 questionBank: 开头的权限）
        for perm in role_perms:
            if perm.endswith(':*') and permission.startswith(perm[:-2] + ':'):
                return True
        
        return False
    
    @staticmethod
    def get_user_permissions(user_role: str) -> List[str]:
        """
        获取用户角色的所有权限列表
        :param user_role: 用户角色
        :return: 权限列表
        """
        if not user_role:
            return []
        
        role_perms = PermissionService.ROLE_PERMISSIONS.get(user_role, [])
        
        # 如果拥有通配符权限，返回所有权限
        if '*' in role_perms:
            return PermissionService.ALL_PERMISSIONS.copy()
        
        return role_perms.copy()
    
    @staticmethod
    def filter_menu_by_permissions(menu: Dict[str, Any], user_role: str) -> Optional[Dict[str, Any]]:
        """
        根据用户权限过滤菜单项
        :param menu: 菜单配置
        :param user_role: 用户角色
        :return: 过滤后的菜单配置，如果无权访问则返回None
        """
        # 复制菜单配置
        filtered_menu = menu.copy()
        
        # 检查是否需要认证
        if menu.get('meta', {}).get('requiresAuth', False):
            # 需要认证的菜单，检查权限
            
            # 检查子菜单权限
            if 'children' in menu and menu['children']:
                filtered_children = []
                for child in menu['children']:
                    # 检查子菜单权限
                    child_permissions = child.get('permissions', [])
                    
                    # 如果没有指定权限，默认需要认证即可访问
                    if not child_permissions:
                        filtered_children.append(child)
                    else:
                        # 检查是否有任一权限
                        has_access = any(
                            PermissionService.has_permission(user_role, perm)
                            for perm in child_permissions
                        )
                        if has_access:
                            filtered_child = child.copy()
                            # 递归处理子菜单的权限信息
                            filtered_child['permissions'] = [
                                perm for perm in child_permissions
                                if PermissionService.has_permission(user_role, perm)
                            ]
                            filtered_children.append(filtered_child)
                
                filtered_menu['children'] = filtered_children
                
                # 如果父菜单有子菜单但过滤后没有子菜单，且父菜单本身不需要特殊权限，仍然返回
                # 但对于需要认证的菜单，如果没有可访问的子菜单，可以隐藏父菜单
                if not filtered_children and menu.get('meta', {}).get('requiresAuth', True):
                    # 如果父菜单需要认证且没有可访问的子菜单，返回None（隐藏）
                    return None
            
            # 检查父菜单权限
            menu_permissions = menu.get('permissions', [])
            if menu_permissions:
                has_access = any(
                    PermissionService.has_permission(user_role, perm)
                    for perm in menu_permissions
                )
                if not has_access:
                    return None
        
        # 处理权限字段，只返回用户拥有的权限
        if 'permissions' in filtered_menu:
            filtered_menu['permissions'] = [
                perm for perm in filtered_menu['permissions']
                if PermissionService.has_permission(user_role, perm)
            ]
        
        return filtered_menu
    
    @staticmethod
    def get_user_menus(user_role: str) -> List[Dict[str, Any]]:
        """
        获取用户可访问的菜单列表
        :param user_role: 用户角色
        :return: 菜单列表
        """
        if not user_role:
            return []
        
        # 获取角色可访问的菜单配置
        role_menus = PermissionService.ROLE_MENUS.get(user_role, [])
        
        # 如果角色有通配符权限，返回所有菜单（但需要根据权限过滤）
        if '*' in role_menus:
            filtered_menus = []
            for menu in PermissionService.ALL_MENUS:
                filtered_menu = PermissionService.filter_menu_by_permissions(menu, user_role)
                if filtered_menu:
                    filtered_menus.append(filtered_menu)
            return filtered_menus
        
        # 根据角色配置的菜单列表过滤
        filtered_menus = []
        for menu in PermissionService.ALL_MENUS:
            menu_name = menu.get('name', '')
            if menu_name in role_menus:
                filtered_menu = PermissionService.filter_menu_by_permissions(menu, user_role)
                if filtered_menu:
                    filtered_menus.append(filtered_menu)
        
        return filtered_menus
    
    @staticmethod
    def get_user_permission_info(user_role: str) -> Dict[str, Any]:
        """
        获取用户的完整权限信息（菜单+操作权限）
        :param user_role: 用户角色
        :return: 权限信息字典
        """
        return {
            'role': user_role,
            'permissions': PermissionService.get_user_permissions(user_role),
            'menus': PermissionService.get_user_menus(user_role)
        }


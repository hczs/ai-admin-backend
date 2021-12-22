from rest_framework import serializers

from authentication.models import Account, Role, Permission


class AccountSerializer(serializers.ModelSerializer):
    """
    创建、更新序列化
    """
    class Meta:
        model = Account
        fields = "__all__"


class AccountListSerializer(serializers.ModelSerializer):

    roles = serializers.StringRelatedField(many=True)

    """
    查询结果返回序列化
    """
    class Meta:
        model = Account
        fields = ['id', 'account_number', 'roles', 'create_time', 'update_time']


class AccountSelectSerializer(serializers.ModelSerializer):
    """
    查询结果返回序列化
    """
    class Meta:
        model = Account
        fields = ['id', 'account_number', 'roles', 'create_time', 'update_time']


class PermissionSerializer(serializers.ModelSerializer):

    type = serializers.ChoiceField(choices=Permission.permission_type_choices, default='interface')

    parent = serializers.StringRelatedField()

    class Meta:
        model = Permission
        fields = "__all__"


class PermissionCreateSerializer(serializers.ModelSerializer):

    type = serializers.ChoiceField(choices=Permission.permission_type_choices, default='interface')

    class Meta:
        model = Permission
        fields = "__all__"

# class RoleSerializer(serializers.ModelSerializer):
#     """
#     弃用
#     """
#
#     permissions_tree = serializers.SerializerMethodField(label='权限树信息')
#
#     class Meta:
#         model = Role
#         fields = ['id', 'name', 'description', 'permissions', 'create_time', 'update_time', 'permissions_tree']
#
#     def get_permissions_tree(self, obj):
#         return get_tree(obj.permissions.values())


class RoleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Role
        fields = "__all__"




from rest_framework import serializers, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum
from .models import AffiliateNode, Commission
from apps.affiliates.models import MAX_COMMISSION_LEVELS


class CommissionSerializer(serializers.ModelSerializer):
    from_user_username = serializers.CharField(source='from_user.username', read_only=True)
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    plan_category = serializers.CharField(source='plan.get_category_display', read_only=True)

    class Meta:
        model = Commission
        fields = [
            'id', 'from_user_username', 'plan_name', 'plan_category',
            'level_depth', 'rate', 'amount_kes', 'amount_usd',
            'status', 'transaction_code', 'plan_purchase_txn', 'paid_at', 'created_at'
        ]


class AffiliateNodeSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = AffiliateNode
        fields = ['id', 'username', 'email', 'depth', 'is_active', 'created_at']


class MyAffiliateNodeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            node = AffiliateNode.objects.get(user=request.user)
        except AffiliateNode.DoesNotExist:
            return Response({'error': 'Affiliate node not found.'}, status=404)

        level_counts = {f'level_{i}': 0 for i in range(1, 9)}

        def count_levels(nodes, current_level):
            if current_level > 8 or not nodes:
                return
            level_counts[f'level_{current_level}'] = len(nodes)
            for n in nodes:
                count_levels(list(n.children.all()), current_level + 1)

        count_levels(list(node.children.all()), 1)

        return Response({
            'node': AffiliateNodeSerializer(node).data,
            'downline_by_level': level_counts,
            'total_downline': sum(level_counts.values()),
        })


class AffiliateTreeView(APIView):
    """Returns the user's referral tree 2 levels deep."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            node = AffiliateNode.objects.get(user=request.user)
        except AffiliateNode.DoesNotExist:
            return Response({'tree': []})

        def serialize_node(n, depth=0):
            children = []
            if depth < 2:
                for child in n.children.select_related('user').all()[:20]:
                    children.append(serialize_node(child, depth + 1))
            return {
                'id': str(n.id),
                'username': n.user.username,
                'depth': n.depth,
                'children': children,
                'joined': n.created_at.isoformat(),
            }

        return Response({'tree': serialize_node(node)})


class DownlineMembersView(APIView):
    """
    Returns the list of members at a specific downline level (1-8).
    Level 1 includes name, email, phone.
    Levels 2-8 include name and email only (for privacy).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, level):
        if level < 1 or level > 8:
            return Response({'error': 'Level must be between 1 and 8.'}, status=400)

        try:
            root_node = AffiliateNode.objects.get(user=request.user)
        except AffiliateNode.DoesNotExist:
            return Response({'members': [], 'count': 0})

        # Traverse the tree to collect nodes at the requested depth
        def get_nodes_at_depth(node, target_depth, current_depth=1):
            if current_depth == target_depth:
                return list(node.children.select_related('user__profile').all())
            results = []
            for child in node.children.all():
                results.extend(get_nodes_at_depth(child, target_depth, current_depth + 1))
            return results

        nodes = get_nodes_at_depth(root_node, level)

        members = []
        for n in nodes:
            u = n.user
            member = {
                'id': str(u.id),
                'username': u.username,
                'name': u.full_name,
                'email': u.email,
                'joined': n.created_at.strftime('%d %b %Y'),
                'is_active': n.is_active,
            }
            # Phone number only visible for direct (L1) referrals
            if level == 1:
                member['phone'] = u.phone or '—'

            members.append(member)

        return Response({
            'level': level,
            'members': members,
            'count': len(members),
        })


class CommissionListView(generics.ListAPIView):
    serializer_class = CommissionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Commission.objects.filter(
            recipient=self.request.user
        ).select_related('from_user', 'plan').order_by('-created_at')


class EarningsSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        commissions = Commission.objects.filter(recipient=user, status=Commission.STATUS_PAID)

        total = commissions.aggregate(
            total_usd=Sum('amount_usd'), total_kes=Sum('amount_kes')
        )
        by_level = {}
        for lvl in range(1, MAX_COMMISSION_LEVELS + 1):
            agg = commissions.filter(level_depth=lvl).aggregate(
                total=Sum('amount_usd')
            )
            by_level[f'level_{lvl}'] = {
                'total_usd': str(agg['total'] or 0),
                'count': commissions.filter(level_depth=lvl).count()
            }

        return Response({
            'total_earned_usd': str(total['total_usd'] or 0),
            'total_earned_kes': str(total['total_kes'] or 0),
            'yields_wallet_balance': str(user.yields_wallet.balance_usd),
            'by_level': by_level,
            'total_commissions': commissions.count(),
        })
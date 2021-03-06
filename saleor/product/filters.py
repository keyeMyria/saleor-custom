from collections import OrderedDict

from django.db.models import Q
from django.forms import CheckboxSelectMultiple, ValidationError
from django.utils.translation import pgettext_lazy
from django_filters import MultipleChoiceFilter, OrderingFilter, RangeFilter
from django_prices.models import MoneyField

from ..core.filters import SortedFilterSet
from .models import Product, ProductAttribute, Category

SORT_BY_FIELDS = OrderedDict([
    ('name', pgettext_lazy('Product list sorting option', 'name')),
    ('price', pgettext_lazy('Product list sorting option', 'price'))])


class ProductFilter(SortedFilterSet):
    sort_by = OrderingFilter(
        label=pgettext_lazy('Product list sorting form', 'Sort by'),
        fields=SORT_BY_FIELDS.keys(),
        field_labels=SORT_BY_FIELDS)

    class Meta:
        model = Product
        fields = ['price']
        filter_overrides = {MoneyField: {'filter_class': RangeFilter}}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.product_attributes, self.variant_attributes = (
            self._get_attributes())
        self.categories = self._get_category()
        self.filters.update(self._get_category_filters())
        self.filters.update(self._get_product_attributes_filters())
        self.filters.update(self._get_product_variants_attributes_filters())
        self.filters = OrderedDict(sorted(self.filters.items()))

    def _get_attributes(self):
        q_product_attributes = self._get_product_attributes_lookup()
        q_variant_attributes = self._get_variant_attributes_lookup()
        product_attributes = (
            ProductAttribute.objects.all()
            .prefetch_related('values')
            .filter(q_product_attributes)
            .distinct())
        variant_attributes = (
            ProductAttribute.objects.all()
            .prefetch_related('values')
            .filter(q_variant_attributes)
            .distinct())
        return product_attributes, variant_attributes

    def _get_product_attributes_lookup(self):
        raise NotImplementedError()

    def _get_variant_attributes_lookup(self):
        raise NotImplementedError()

    def _get_product_attributes_filters(self):
        filters = {}
        for attribute in self.product_attributes:
            filters[attribute.slug] = MultipleChoiceFilter(
                name='attributes__%s' % attribute.pk,
                label=attribute.name,
                widget=CheckboxSelectMultiple,
                choices=self._get_attribute_choices(attribute))
        return filters

    def _get_category(self):
        return []

    def _get_category_filters(self):
        filters = {}
        if self.categories:
            filters['category'] = MultipleChoiceFilter(
                name='__category',
                label='Category',
                widget=CheckboxSelectMultiple,
                choices=self._get_category_choices(self.categories))
        return filters

    def _get_category_choices(self,categories):
        return [(choice.pk, choice.name) for choice in categories]

    def _get_product_variants_attributes_filters(self):
        filters = {}
        for attribute in self.variant_attributes:
            filters[attribute.slug] = MultipleChoiceFilter(
                name='variants__attributes__%s' % attribute.pk,
                label=attribute.name,
                widget=CheckboxSelectMultiple,
                choices=self._get_attribute_choices(attribute))
        return filters

    def _get_attribute_choices(self, attribute):
        return [(choice.pk, choice.name) for choice in attribute.values.all()]

    def validate_sort_by(self, value):
        if value.strip('-') not in SORT_BY_FIELDS:
            raise ValidationError(
                pgettext_lazy(
                    'Validation error for sort_by filter',
                    '%(value)s is not a valid sorting option'),
                params={'value': value})


class ProductCategoryFilter(ProductFilter):
    def __init__(self, *args, **kwargs):
        self.category = kwargs.pop('category')
        self.attribute = kwargs.pop('attributes')
        self.values = kwargs.pop('values')
        super().__init__(*args, **kwargs)

    def _get_categoy(self):
        return Category.objects.filter(id__in=self.category)

    def _get_product_attributes_lookup(self):
        return Q(product_types__products__category__in=self.category)&Q(name__in=self.attribute)

    def _get_variant_attributes_lookup(self):
        return Q(product_variant_types__products__category__in=self.category)&Q(name__in=self.attribute)

    def _get_attribute_choices(self,attribute):
        return [(choice.pk, choice.name) for choice in attribute.values.filter(id__in=self.values)]

class ProductBrandFilter(ProductFilter):
    def __init__(self, *args, **kwargs):
        self.category = kwargs.pop('category')
        self.attribute = kwargs.pop('attributes')
        super().__init__(*args, **kwargs)

    def _get_category(self):
        return Category.objects.filter(id__in=self.category)

    def _get_product_attributes_lookup(self):
        return Q(product_types__products__category__in=self.category)&Q(name__in=self.attribute)

    def _get_variant_attributes_lookup(self):
        return Q(product_variant_types__products__category__in=self.category)&Q(name__in=self.attribute)

class ProductCollectionFilter(ProductFilter):
    def __init__(self, *args, **kwargs):
        self.collection = kwargs.pop('collection')
        super().__init__(*args, **kwargs)

    def _get_product_attributes_lookup(self):
        return Q(product_types__products__collections=self.collection)

    def _get_variant_attributes_lookup(self):
        return Q(product_variant_types__products__collections=self.collection)

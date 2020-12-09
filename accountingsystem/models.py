from django.db import models

class Account(models.Model):
    acc_id = models.AutoField(primary_key=True)
    acc_name = models.CharField(max_length=50)
    acc_parent = models.ForeignKey('self', models.DO_NOTHING, db_column='acc_parent', blank=True, null=True)
    acc_level = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'account'
        unique_together = (('acc_id', 'acc_name'),)


class Adjentry(models.Model):
    adj_id = models.AutoField(primary_key=True)
    amount = models.DecimalField(max_digits=22, decimal_places=2)
    adj_num = models.IntegerField()
    pre = models.ForeignKey('Preamt', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'adjentry'


class Cashinbanks(models.Model):
    cash_in_banks_id = models.AutoField(primary_key=True)
    bank_name = models.CharField(max_length=50)
    bank_account_number = models.CharField(max_length=5)
    type = models.ForeignKey(Account, models.DO_NOTHING, db_column='type')
    currency = models.CharField(max_length=10)
    foreign_currency_amount = models.DecimalField(max_digits=22, decimal_places=2, blank=True, null=True)
    ntd_amount = models.DecimalField(max_digits=22, decimal_places=2)
    rpt = models.ForeignKey('Report', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'cashinbanks'


class Company(models.Model):
    com_id = models.AutoField(primary_key=True)
    com_name = models.CharField(max_length=50)
    com_parent = models.ForeignKey('self', models.DO_NOTHING, db_column='com_parent', blank=True, null=True)
    parent_ratio = models.DecimalField(max_digits=6, decimal_places=4, blank=True, null=True)
    currency = models.CharField(max_length=10)
    grp = models.ForeignKey('Group', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'company'
        unique_together = (('com_id', 'com_name'),)


class Depositaccount(models.Model):
    dep_acc_id = models.AutoField(primary_key=True)
    bank_name = models.CharField(max_length=50)
    bank_account_number = models.CharField(max_length=5)
    currency = models.CharField(max_length=10)
    foreign_currency_amount = models.DecimalField(max_digits=22, decimal_places=2, blank=True, null=True)
    ntd_amount = models.DecimalField(max_digits=22, decimal_places=2)
    plege = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    rpt = models.ForeignKey('Report', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'depositaccount'


class Disclosure(models.Model):
    disclosure_id = models.AutoField(primary_key=True)
    pre_amt = models.DecimalField(max_digits=22, decimal_places=2)
    dis_detail = models.ForeignKey('Disdetail', models.DO_NOTHING)
    pre = models.ForeignKey('Preamt', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'disclosure'


class Disdetail(models.Model):
    dis_detail_id = models.AutoField(primary_key=True)
    row_name = models.CharField(max_length=50)
    row_amt = models.DecimalField(max_digits=22, decimal_places=2)
    dis_title = models.ForeignKey('Distitle', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'disdetail'


class Distitle(models.Model):
    dis_title_id = models.AutoField(primary_key=True)
    dis_name = models.CharField(max_length=50)
    rpt = models.ForeignKey('Report', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'distitle'


class Exchangerate(models.Model):
    rate_id = models.AutoField(primary_key=True)
    currency_name = models.CharField(max_length=10)
    rate = models.DecimalField(max_digits=8, decimal_places=5)
    pre = models.ForeignKey('Preamt', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'exchangerate'


class Group(models.Model):
    grp_id = models.AutoField(primary_key=True)
    grp_name = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'group'
        unique_together = (('grp_id', 'grp_name'),)


class Preamt(models.Model):
    pre_id = models.AutoField(primary_key=True)
    book_amt = models.DecimalField(max_digits=22, decimal_places=2)
    adj_mat = models.DecimalField(max_digits=22, decimal_places=2)
    pre_amt = models.DecimalField(max_digits=22, decimal_places=2)
    rpt = models.ForeignKey('Report', models.DO_NOTHING)
    acc = models.ForeignKey('Account', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'preamt'


class Reltrx(models.Model):
    rel_id = models.AutoField(primary_key=True)
    target = models.ForeignKey(Company, models.DO_NOTHING, db_column='target')
    related_amt = models.DecimalField(max_digits=22, decimal_places=2)
    pre = models.ForeignKey('Preamt', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'reltrx'


class Report(models.Model):
    rpt_id = models.AutoField(primary_key=True)
    start_date = models.DateField()
    end_date = models.DateField()
    type = models.CharField(max_length=2)
    com = models.ForeignKey('Company', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'report'


class Systemcode(models.Model):
    system_code_id = models.AutoField(primary_key=True)
    code_type = models.CharField(max_length=20)
    system_code = models.CharField(max_length=10)
    code_name = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'systemcode'
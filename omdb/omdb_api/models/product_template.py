from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = "product.template"

    year = fields.Char(string="Année")  # Moche mais vrai info.
    run_time = fields.Char(string="Durée")
    meta_score = fields.Integer(string="MetaScore (0-100)")
    actors = fields.Text(string="Acteur(s)")

    meta_score_display = fields.Html(
        "Meta Score", compute="_compute_meta_score_display"
    )

    @api.depends("meta_score")
    def _compute_meta_score_display(self):
        self.meta_score_display = "{} /100".format(self.meta_score)

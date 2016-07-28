# -*- coding: utf-8 -*-
# Copyright (C) 2010 Savoir-faire Linux (<http://www.savoirfairelinux.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.tests import common
from openerp.exceptions import ValidationError


class TestModelNonConformity(common.TransactionCase):

    def setUp(self):
        super(TestModelNonConformity, self).setUp()
        self.nc_model = self.env['mgmtsystem.nonconformity']
        self.partner = self.env['res.partner'].search([])[0]
        self.nc_test = self.nc_model.create({
            'partner_id': self.partner.id,
            'manager_user_id': self.env.user.id,
            'description': "description",
            'responsible_user_id': self.env.user.id,
            })
        action_vals = {'name': 'An Action', 'type_action': 'correction'}
        action1 = self.nc_model.action_ids.create(action_vals)
        self.nc_test.corrective_action_id = action1

    def test_open_validation(self):
        """Don't allow approving/In Progress action comments"""
        open_stage = self.env.ref('mgmtsystem_nonconformity.stage_open')
        with self.assertRaises(ValidationError):
            self.nc_test.stage_id = open_stage

    def test_done_validation(self):
        """Don't allow closing an NC without evaluation comments"""
        done_stage = self.env.ref('mgmtsystem_nonconformity.stage_done')
        with self.assertRaises(ValidationError):
            self.nc_test.stage_id = done_stage

    def test_done_actions_validation(self):
        """Don't allow closing an NC with open actions"""
        done_stage = self.env.ref('mgmtsystem_nonconformity.stage_done')
        self.nc_test.evaluation_comments = 'OK!'
        with self.assertRaises(ValidationError):
            self.nc_test.stage_id = done_stage

    def test_state_transition(self):
        """Close and reopen Nonconformity"""
        self.nc_test.action_comments = 'OK!'
        self.nc_test.stage_id = self.env.ref(
            'mgmtsystem_nonconformity.stage_open')
        self.assertEqual(
            self.nc_test.corrective_action_id.stage_id,
            self.env.ref('mgmtsystem_action.stage_open'),
            'Plan Approval starts Actions')

        self.nc_test.evaluation_comments = 'OK!'
        self.nc_test.corrective_action_id.stage_id = \
            self.env.ref('mgmtsystem_action.stage_close')
        self.nc_test.stage_id = self.env.ref(
            'mgmtsystem_nonconformity.stage_done')
        self.assertEqual(self.nc_test.state, 'done')
        self.assertTrue(
            self.nc_test.closing_date, 'Set close date on Done')

        self.nc_test.stage_id = self.env.ref(
            'mgmtsystem_nonconformity.stage_open')
        self.assertEqual(self.nc_test.state, 'open')
        self.assertFalse(
            self.nc_test.closing_date, 'Reset close date on reopen')

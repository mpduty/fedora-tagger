# -*- coding: utf-8 -*-

from sqlalchemy import *
from sqlalchemy.orm import mapper, relation
from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import Integer, Unicode
from sqlalchemy.orm import relation, backref

from fedoratagger.model import DeclarativeBase, metadata, DBSession


def tag_sorter(tag1, tag2):
    """ The tag list for each package should be sorted in descending order by
    the total score, ties are broken by the number of votes cast and if there is
    still a tie, alphabetically by the tag.
    """
    for attr in ['total', 'votes', 'label']:
        result = cmp(getattr(tag1, attr), getattr(tag2, attr))
        if result != 0:
            return result
    return result

association_table = Table(
    'package_tag_association', DeclarativeBase.metadata,
    Column('package_id', Integer, ForeignKey('package.id')),
    Column('tag_label_id', Integer, ForeignKey('tag_label.id')),
)

class Package(DeclarativeBase):
    __tablename__ = 'package'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255), nullable=False)
    tags = relation('Tag', backref=('package'))
    tag_labels = relation(
        'TagLabel', backref=('packages'),
        secondary=association_table
    )

    @property
    def summary(self):
        return "No summaries yet."

    def __unicode__(self):
        return self.name

    def __json__(self):
        """ JSON.. kinda. """
        return {
            self.name: [repr(tag) for tag in sorted(self.tags, tag_sorter)]
        }

    def __jit_data__(self):
        return {
            'hover_html' :
            u"<h2>Package: {name}</h2><ul>" + \
            " ".join([
                "<li>{tag.label.label} - {tag.like} / {tag.dislike}</li>".format(
                    tag=tag) for tag in self.tags
            ]) + "</ul>"
        }


class TagLabel(DeclarativeBase):
    __tablename__ = 'tag_label'
    id = Column(Integer, primary_key=True)
    label = Column(Unicode(255), nullable=False)
    tags = relation('Tag', backref=('label'))

    def __unicode__(self):
        return self.label


class Tag(DeclarativeBase):
    __tablename__ = 'tag'
    id = Column(Integer, primary_key=True)
    package_id = Column(Integer, ForeignKey('package.id'))
    label_id = Column(Integer, ForeignKey('tag_label.id'))

    like = Column(Integer, default=1)
    dislike = Column(Integer, default=0)

    @property
    def total(self):
        return self.like - self.dislike

    @property
    def votes(self):
        return self.like + self.dislike

    def __unicode__(self):
        return self.label.label + " on " + self.package.name

    def __json__(self):
        return {
            'tag': self.label.label,
            'like': self.like,
            'dislike': self.dislike,
            'total': self.total,
            'votes': self.votes,
        }

    def __jit_data__(self):
        return {
            'hover_html' :
            u""" <h2>Tag: {label}</h2>
            <ul>
                <li>Likes: {like}</li>
                <li>Dislike: {dislike}</li>
                <li>Total: {total}</li>
                <li>Votes: {votes}</li>
            </ul>
            """.format(
                label=unicode(self),
                like=self.like,
                dislike=self.dislike,
                total=self.total,
                votes=self.votes,
            )
        }
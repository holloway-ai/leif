

from app import schemas

existing_collections = [
    schemas.Collection( name='Collection_1',
                        description="I am a Collection 1",
                        documents=[{"path": "holloway-whitepaper",
                                    "localeCode": "en",
                                    "title": "Holloway Justpaper",
                                    "description": "",
                                    "render": " bla-bla"
                                    },
                                    {
                                    "path": "holloway-justpaper 1",
                                    "localeCode": "en",
                                    "title": "Holloway Whitepaper",
                                    "description": "",
                                    "render": " bla-bla 1"
                                    },
                                    {
                                    "path": "holloway-justpaper 2",
                                    "localeCode": "en",
                                    "title": "Holloway Whitepaper",
                                    "description": "",
                                    "render": " just bla-bla 2"
                                    }],
                        ids = ["holloway-whitepaper", "holloway-justpaper 1", "holloway-justpaper 2" ] ),
    schemas.Collection( name='Collection_2',
                        description="I am a Collection 2",
                        documents=[{"path": "holloway-whitepaper",
                                    "localeCode": "en",
                                    "title": "Holloway Justpaper",
                                    "description": "",
                                    "render": " bla-bla"
                                    },
                                    {
                                    "path": "holloway-justpaper 2",
                                    "localeCode": "en",
                                    "title": "Holloway Whitepaper",
                                    "description": "",
                                    "render": " bla-bla 2"
                                    },
                                    {
                                    "path": "holloway-justpaper 3",
                                    "localeCode": "en",
                                    "title": "Holloway Whitepaper",
                                    "description": "",
                                    "render": " just bla-bla 3"
                                    }],
                        ids = ["holloway-whitepaper", "holloway-justpaper 2", "holloway-justpaper 3" ] )                  
]